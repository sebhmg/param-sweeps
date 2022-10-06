#  Copyright (c) 2022 Mira Geoscience Ltd.
#
#  This file is part of param-sweeps.
#
#  param-sweeps is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

from __future__ import annotations

import os
import argparse
import itertools
import subprocess
import uuid
import json
import numpy as np

from copy import deepcopy
from inspect import signature
from dataclasses import dataclass
from geoh5py.ui_json import InputFile
from geoh5py.workspace import Workspace
from geoh5py.data import Data
from geoh5py.shared.exceptions import BaseValidationError
from sweeps.constants import default_ui_json

@dataclass
class SweepParams:
    """Parameterizes a sweep of the worker driver."""

    title: str = "Parameter sweep"
    run_command: str = "sweeps.driver"
    conda_environment: str = "sweeps"
    monitoring_directory: str = None
    workspace_geoh5: Workspace = None
    geoh5: Workspace = None
    _worker_uijson: str = None

    @classmethod
    def from_input_file(cls, ifile: InputFile):
        """Instantiate params class with contents of input file data."""

        cls_fields = [field for field in signature(cls).parameters]
        base_params, app_params = {}, {}

        for k, v in ifile.data.items():
            if k in cls_fields:
                base_params[k] = v
            else:
                app_params[k] = v

        val = cls(**base_params)
        for k, v in app_params.items():
            setattr(val, k, v)

        return val

    @property
    def worker_uijson(self):
        if self._worker_uijson is None:
            self._worker_uijson = self.geoh5.h5file.replace("_sweep", "")
            self._worker_uijson = self._worker_uijson.replace(".ui.geoh5", ".ui.json")
        return self._worker_uijson

    def worker_parameters(self) -> List[str]:
        """Return all sweep parameter names."""
        return [k.replace("_start", "") for k in self.__dict__ if k.endswith("_start")]

    def parameter_sets(self) -> dict[str, list[int | float]]:
        """Return sets of parameter values that will be combined to form the sweep."""
        names = self.worker_parameters()
        sets = {n: (getattr(self, f"{n}_start"), getattr(self, f"{n}_end"), getattr(self, f"{n}_n")) for n in names}
        sets = {k: [v[0]] if v[1] is None else np.linspace(*v, dtype=int).tolist() for k, v in sets.items()}
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

    def run(self):
        """Execute a sweep."""

        ifile = InputFile.read_ui_json(self.params.worker_uijson)
        workspace = ifile.workspace.open(mode='r')
        sets = self.params.parameter_sets()
        iterations = list(itertools.product(*sets.values()))
        print(f"Running parameter sweep for {len(iterations)} trials of the {ifile.data['title']} driver.")

        param_lookup = {}
        count = 0
        for iter in iterations:
            count += 1
            root_dir = os.path.dirname(workspace.h5file)
            _ = os.path.basename(workspace.h5file).split('.')[0]
            param_uuid = SweepDriver.uuid_from_params(iter)
            filepath = os.path.join(root_dir, f"{param_uuid}.ui.geoh5")
            param_lookup[param_uuid] = dict(zip(sets.keys(), iter))
            lookup_path = os.path.join(root_dir, "lookup.json")

            if os.path.exists(filepath):
                print(f"{count}: Skipping trial: {param_uuid}. Already computed and saved to file.")
                continue
            else:
                print(f"{count}: Running trial: {param_uuid}. Use lookup.json to map uuid to parameter set.")
                with Workspace(filepath) as ws:
                    ifile.data.update(dict(param_lookup[param_uuid], **{"geoh5": ws}))
                    objs = [v for v in ifile.data.values() if hasattr(v, "uid")]
                    for o in objs:
                        if not isinstance(o, Data):
                            o.copy(parent=ws, copy_children=True)

                if os.path.exists(lookup_path):
                    with open(lookup_path, 'r') as f:
                        param_lookup.update(json.load(f))

                with open(lookup_path, 'w') as f:
                    json.dump(param_lookup, f, indent=4)

                ifile.name = f"{param_uuid}.ui.json"
                ifile.path = root_dir
                ifile.write_ui_json()

                conda_env = ifile.data["conda_environment"]
                run_cmd = ifile.data["run_command"]
                subprocess.run([
                    "conda.bat", "activate", conda_env, "&&",
                    "python", "-m", run_cmd, ifile.path_name
                ])

        workspace.close()

def sweep_forms(param: str, value: int | float) -> dict:
    """
    Return a set of three ui.json entries for start, end and n (samples).

    :param param: Parameter name
    :param value: Parameter value
    """
    group = param.replace('_', ' ').capitalize()
    forms = {
        f"{param}_start": {
            "main": True,
            "group": group,
            "label": "starting",
            "value": value,
        },
        f"{param}_end": {
            "main": True,
            "group": group,
            "optional": True,
            "enabled": False,
            "label": "ending",
            "value": value,
        },
        f"{param}_n": {
            "main": True,
            "group": group,
            "dependency": f"{param}_end",
            "dependencyType": "enabled",
            "enabled": False,
            "label": "number of samples",
            "value": 1
        }
    }

    return forms

def generate(file: str, parameters: List[str] = None):
    """
    Generate an *_sweep.ui.json file to sweep parameters of the driver associated with 'file'.

    :param file: Name of .ui.json file
    :param parameters: Parameters to include in the _sweep.ui.json file
    """

    ifile = InputFile.read_ui_json(file)
    sweepfile = InputFile(
        ui_json = deepcopy(default_ui_json),
        validation_options={"disabled": True}
    )

    for k, v in ifile.data.items():

        if parameters is not None and k not in parameters:
            continue

        if type(v) in [int, float]:
            forms = sweep_forms(k, v)
            sweepfile.ui_json.update(forms)

    sweepfile.data["geoh5"] = ifile.data["geoh5"]
    dirname = os.path.dirname(ifile.data["geoh5"].h5file)
    filename = os.path.basename(ifile.data["geoh5"].h5file)
    filename = filename.replace(".ui", "")
    filename = filename.replace(".geoh5", "_sweep.ui.json")
    sweepfile.write_ui_json(
        name=filename,
        path=dirname
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run parameter sweep of worker driver.")
    parser.add_argument("file", help="File with ui.json format.")
    parser.add_argument(
        "--generate",
        help="Generate a sweeper ui.json from the worker ui.json.",
        action="store_true"
    )
    parser.add_argument(
        "--parameters",
        help="List of parameters to be included as sweep parameters.",
        nargs='+'
    )

    args = parser.parse_args()
    filepath = args.file

    if filepath.endswith("ui.json"):
        try:
            InputFile.read_ui_json(filepath)
        except BaseValidationError as e:
            raise IOError(f"File argument {filepath} is not a valid ui.json file.") from e
    else:
        raise IOError(f"File argument {filepath} must have extension 'ui.json'.")

    if args.generate:
        generate(filepath, parameters=args.parameters)
    else:

        print("Reading parameters and workspace...")
        if "_sweep" not in filepath:
            filepath = filepath.replace(".ui.json", "_sweep.ui.json")
        ifile = InputFile.read_ui_json(filepath)
        params = SweepParams.from_input_file(ifile)
        SweepDriver(params).run()
