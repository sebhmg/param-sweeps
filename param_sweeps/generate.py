#  Copyright (c) 2022 Mira Geoscience Ltd.
#
#  This file is part of param-sweeps.
#
#  param-sweeps is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

from __future__ import annotations

import argparse
import os
from copy import deepcopy

from geoh5py.ui_json import InputFile

from param_sweeps.constants import default_ui_json


def generate(worker: str, parameters: list[str] = None, update_values: dict = None):
    """
    Generate an *_sweep.ui.json file to sweep parameters of the driver associated with 'file'.

    :param file: Name of .ui.json file
    :param parameters: Parameters to include in the _sweep.ui.json file
    :param update_values: Updates for sweep files parameters
    """

    file = os.path.abspath(worker)
    ifile = InputFile.read_ui_json(file)
    sweepfile = InputFile(
        ui_json=deepcopy(default_ui_json), validation_options={"disabled": True}
    )
    sweepfile.data.update({"worker_uijson": worker})
    if update_values:
        sweepfile.data.update(**update_values)

    for param, value in ifile.data.items():

        if parameters is not None and param not in parameters:
            continue

        if type(value) in [int, float]:
            forms = sweep_forms(param, value)
            sweepfile.ui_json.update(forms)

    sweepfile.data["geoh5"] = ifile.data["geoh5"]
    dirname = os.path.dirname(file)
    filename = os.path.basename(file)
    filename = filename.rstrip("ui.json")
    filename = filename.rstrip("_sweep")
    filename = f"{filename}_sweep.ui.json"

    print(f"Writing sweep file to: {os.path.join(dirname, filename)}")
    sweepfile.write_ui_json(name=filename, path=dirname)


def sweep_forms(param: str, value: int | float) -> dict:
    """
    Return a set of three ui.json entries for start, end and n (samples).

    :param param: Parameter name
    :param value: Parameter value
    """
    group = param.replace("_", " ").capitalize()
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
            "value": 1,
        },
    }

    return forms


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a sweep file.")
    parser.add_argument("file", help="File with ui.json format.")
    parser.add_argument(
        "--parameters",
        help="List of parameters to be included as sweep parameters.",
        nargs="+",
    )
    args = parser.parse_args()
    generate(args.file, args.parameters)
