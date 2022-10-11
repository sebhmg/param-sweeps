#  Copyright (c) 2022 Mira Geoscience Ltd.
#
#  This file is part of param-sweeps.
#
#  param-sweeps is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

from __future__ import annotations

import argparse
import itertools
import json
import os
import subprocess
import uuid
from dataclasses import dataclass
from inspect import signature

import numpy as np
from geoh5py.data import Data
from geoh5py.shared.exceptions import BaseValidationError
from geoh5py.ui_json import InputFile
from geoh5py.workspace import Workspace


@dataclass
class SweepParams:
    """Parametrizes a sweep of the worker driver."""

    title: str = "Parameter sweep"
    run_command: str = "sweeps.driver"
    conda_environment: str = "sweeps"
    monitoring_directory: str | None = None
    workspace_geoh5: Workspace | None = None
    geoh5: Workspace | None = None
    _worker_uijson: str | None = None

    @classmethod
    def from_input_file(cls, ifile: InputFile):
        """Instantiate params class with contents of input file data."""

        cls_fields = list(signature(cls).parameters)
        base_params, app_params = {}, {}

        for param, value in ifile.data.items():
            if param in cls_fields:
                base_params[param] = value
            else:
                app_params[param] = value

        val = cls(**base_params)
        for param, value in app_params.items():
            setattr(val, param, value)

        return val

    @property
    def worker_uijson(self):

        if self._worker_uijson is None:
            root = os.path.dirname(self.geoh5.h5file)
            file = os.path.basename(self.geoh5.h5file)
            file = file.replace("_sweep", "")
            file = file.replace(".ui.geoh5" if ".ui." in file else ".geoh5", ".ui.json")
            self._worker_uijson = os.path.join(root, file)

        return self._worker_uijson

    def worker_parameters(self) -> list[str]:
        """Return all sweep parameter names."""
        return [k.replace("_start", "") for k in self.__dict__ if k.endswith("_start")]

    def parameter_sets(self) -> dict:
        """Return sets of parameter values that will be combined to form the sweep."""
        names = self.worker_parameters()
        sets = {
            n: (
                getattr(self, f"{n}_start"),
                getattr(self, f"{n}_end"),
                getattr(self, f"{n}_n"),
            )
            for n in names
        }
        sets = {
            k: [v[0]] if v[1] is None else np.linspace(*v).tolist()
            for k, v in sets.items()
        }
        return sets


class SweepDriver:
    """Sweeps parameters of a worker driver."""

    def __init__(self, params):
        self.params: SweepParams = params

    @staticmethod
    def uuid_from_params(params: tuple) -> str:
        """
        Create a deterministic uuid.

        :param params: Tuple containing the values of a sweep iteration.

        :returns: Unique but recoverable uuid file identifier string.
        """
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(hash(params))))

    def run(self, files_only=False):
        """Execute a sweep."""

        ifile = InputFile.read_ui_json(self.params.worker_uijson)
        workspace = ifile.data["geoh5"].open(mode="r")
        sets = self.params.parameter_sets()
        iterations = list(itertools.product(*sets.values()))
        print(
            f"Running parameter sweep for {len(iterations)} "
            f"trials of the {ifile.data['title']} driver."
        )

        param_lookup = {}
        for count, iteration in enumerate(iterations):
            param_uuid = SweepDriver.uuid_from_params(iteration)
            filepath = os.path.join(
                os.path.dirname(workspace.h5file), f"{param_uuid}.ui.geoh5"
            )
            param_lookup[param_uuid] = dict(zip(sets.keys(), iteration))

            if os.path.exists(filepath):
                print(
                    f"{count}: Skipping trial: {param_uuid}. "
                    f"Already computed and saved to file."
                )
                continue

            print(
                f"{count}: Running trial: {param_uuid}. "
                f"Use lookup.json to map uuid to parameter set."
            )
            with Workspace(filepath) as iter_workspace:
                ifile.data.update(
                    dict(param_lookup[param_uuid], **{"geoh5": iter_workspace})
                )
                objects = [v for v in ifile.data.values() if hasattr(v, "uid")]
                for obj in objects:
                    if not isinstance(obj, Data):
                        obj.copy(parent=iter_workspace, copy_children=True)

            update_lookup(param_lookup, workspace)

            ifile.name = f"{param_uuid}.ui.json"
            ifile.path = os.path.dirname(workspace.h5file)
            ifile.write_ui_json()

            if not files_only:
                call_worker_subprocess(ifile)

        workspace.close()


def call_worker_subprocess(ifile: InputFile):
    """Runs the worker for the sweep parameters contained in 'ifile'."""
    conda_env = ifile.data["conda_environment"]
    run_cmd = ifile.data["run_command"]
    subprocess.run(
        [
            "conda.bat",
            "activate",
            conda_env,
            "&&",
            "python",
            "-m",
            run_cmd,
            ifile.path_name,
        ],
        check=True,
    )


def update_lookup(lookup: dict, workspace: Workspace):
    """Updates lookup with new entries. Ensures any previous runs are incorporated."""
    lookup_path = os.path.join(os.path.dirname(workspace.h5file), "lookup.json")
    if os.path.exists(lookup_path):  # In case restarting
        with open(lookup_path) as file:
            lookup.update(json.load(file))

    with open(lookup_path, "w") as file:
        json.dump(lookup, file, indent=4)

    return lookup


def file_validation(filepath):
    """Validate file."""
    if filepath.endswith("ui.json"):
        try:
            InputFile.read_ui_json(filepath)
        except BaseValidationError as err:
            raise OSError(
                f"File argument {filepath} is not a valid ui.json file."
            ) from err
    else:
        raise OSError(f"File argument {filepath} must have extension 'ui.json'.")


def main(file_path, files_only=False):
    """Run the program."""

    file_validation(file_path)
    print("Reading parameters and workspace...")
    if "_sweep" not in file_path:
        file_path = file_path.replace(".ui.json", "_sweep.ui.json")
    input_file = InputFile.read_ui_json(file_path)
    sweep_params = SweepParams.from_input_file(input_file)
    SweepDriver(sweep_params).run(files_only)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Run parameter sweep of worker driver."
    )
    parser.add_argument("file", help="File with ui.json format.")

    args = parser.parse_args()
    main(args.file)
