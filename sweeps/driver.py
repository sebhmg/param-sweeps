import os
import argparse
import itertools
import subprocess
import uuid
import json

from geoh5py.ui_json import InputFile
from geoh5py.workspace import Workspace
from geoh5py.data import Data
from geoh5py.shared.exceptions import BaseValidationError
from sweeps.params import SweepParams


class SweepDriver:

    def __init__(self, params):
        self.params = params

    def run(self):

        ifile = InputFile.read_ui_json(self.params.worker_uijson)
        ifile.workspace.open(mode='r')
        sets = self.params.parameter_sets()
        iterations = list(itertools.product(*sets.values()))
        print(f"Running parameter sweep for {len(iterations)} trials of the {ifile.data['title']} driver.")

        param_lookup = {}
        count = 0
        for iter in iterations:
            count += 1
            root_dir = os.path.dirname(ifile.workspace.h5file)
            root_name = os.path.basename(ifile.workspace.h5file).split('.')[0]
            param_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(hash(iter))))
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




def sweep_forms(param, value):
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

def generate(file, parameters=None):
    """Generate a ui.json file to sweep parameter in 'file' driver."""

    ifile = InputFile.read_ui_json(file)
    sweepfile = InputFile.read_ui_json(
        os.path.join(os.path.dirname(__file__), "template.ui.json"),
        validation_options={"disabled": True}
    )
    for k, v in ifile.data.items():

        if parameters is not None and k not in parameters:
            continue

        if type(v) in [int, float]:
            forms = sweep_forms(k, v)
            sweepfile.ui_json.update(forms)

    sweepfile.data["geoh5"] = ifile.data["geoh5"]
    sweepfile.data["worker_uijson"] = os.path.abspath(file)
    # sweepfile.data["result_name"] = ifile.data.get("out_group", None)
    sweepfile.write_ui_json(
        name=os.path.basename(ifile.data["geoh5"].h5file).replace(".ui.geoh5", "_sweep.ui.json"),
        path=os.path.dirname(ifile.data["geoh5"].h5file)
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
        params = SweepParams(ifile)
        SweepDriver(params).run()
