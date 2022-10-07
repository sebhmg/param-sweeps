#  Copyright (c) 2022 Mira Geoscience Ltd.
#
#  This file is part of param-sweeps.
#
#  param-sweeps is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

import itertools
import json
import os
from copy import deepcopy
from dataclasses import dataclass

import numpy as np
import pytest
from geoh5py.objects import Points
from geoh5py.ui_json import InputFile
from geoh5py.workspace import Workspace

from sweeps.constants import default_ui_json
from sweeps.driver import (SweepDriver, SweepParams, file_validation, generate,
                           main, sweep_forms, update_lookup)


def test_params(tmp_path):
    workspace = Workspace(os.path.join(tmp_path, "worker.ui.geoh5"))
    test = deepcopy(default_ui_json)
    test.update(
        {
            "geoh5": workspace.h5file,
            "param1_start": {"label": "param1 start", "value": 1},
            "param1_end": {"label": "param1 end", "value": 2},
            "param1_n": {"label": "param1 n samples", "value": 2},
        }
    )
    ifile = InputFile(ui_json=test)
    params = SweepParams.from_input_file(ifile)
    _ = SweepDriver(params)

    assert os.path.split(params.worker_uijson)[-1] == "worker.ui.json"
    worker_params = params.worker_parameters()
    assert len(worker_params) == 1
    assert worker_params[0] == "param1"
    psets = params.parameter_sets()
    assert len(psets) == 1
    assert "param1" in psets
    assert psets["param1"] == [1, 2]


def test_update_lookup(tmp_path):
    workspace = Workspace(os.path.join(tmp_path, "test.geoh5"))
    test = {"first entry": {"param1": 2, "param2": 1}}
    with open(os.path.join(tmp_path, "lookup.json"), "w", encoding="utf-8") as file:
        json.dump(test, file, ensure_ascii=False, indent=4)

    lookup = {"second entry": {"param1": 1, "param2": 2}}
    new_lookup = update_lookup(lookup, workspace)
    assert new_lookup == dict(test, **lookup)


def test_uuid_from_params():
    test = {"a": [1, 2], "b": [3, 4], "c": [5, 6]}
    iterations = list(itertools.product(*test.values()))
    for iteration in iterations:
        trial_uuid = SweepDriver.uuid_from_params(iteration)
        assert trial_uuid == SweepDriver.uuid_from_params(
            iteration
        ), "method is not deterministic"


def test_sweep_forms():
    forms = sweep_forms("test", 1)
    params = ["test_start", "test_end", "test_n"]
    assert len(forms) == 3
    assert all(k in forms for k in params)
    assert all(forms[k]["group"] == "Test" for k in params)
    assert all(f["value"] == 1 for f in forms.values())
    assert forms["test_end"]["optional"]
    assert not forms["test_end"]["enabled"]
    assert forms["test_n"]["dependency"] == "test_end"
    assert forms["test_n"]["dependencyType"] == "enabled"
    assert not forms["test_n"]["enabled"]


def test_generate(tmp_path):
    workspace = Workspace(os.path.join(tmp_path, "worker.ui.geoh5"))

    test = deepcopy(default_ui_json)
    test.update(
        {
            "geoh5": workspace.h5file,
            "param1": {"label": "param1", "value": 1},
            "param2": {"label": "param2", "value": 2.5},
        }
    )

    path = os.path.join(tmp_path, "worker.ui.json")
    with open(path, "w", encoding="utf8") as file:
        json.dump(test, file, indent=4)

    generate(path)
    with open(path.replace(".ui.json", "_sweep.ui.json")) as file:
        data = json.load(file)

    assert "param1_start" in data
    assert "param1_end" in data
    assert "param1_n" in data
    assert "param2_start" in data
    assert "param2_end" in data
    assert "param2_n" in data

    assert not data["param1_end"]["enabled"]
    assert not data["param1_n"]["enabled"]
    assert data["param1_n"]["dependency"] == "param1_end"
    assert not data["param2_end"]["enabled"]
    assert not data["param2_n"]["enabled"]
    assert data["param2_n"]["dependency"] == "param2_end"

    generate(path, parameters=["param1"])

    with open(path.replace(".ui.json", "_sweep.ui.json")) as file:
        data = json.load(file)

    assert "param2_start" not in data
    assert "param2_end" not in data
    assert "param2_n" not in data


def test_file_validation(tmp_path):

    filepath = os.path.join(tmp_path, "test.json")
    open(filepath, "w", encoding="utf-8").close()  # pylint: disable=R1732
    with pytest.raises(OSError) as excinfo:
        file_validation(filepath)

    assert all(s in str(excinfo.value) for s in [filepath, "ui.json"])

    filepath = filepath.replace(".json", ".ui.json")
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump({}, file)

    with pytest.raises(OSError) as excinfo:
        file_validation(filepath)

    assert all(s in str(excinfo.value) for s in [filepath, "not a valid"])


def test_sweep(tmp_path):  # pylint: disable=R0914

    geoh5_path = os.path.join(tmp_path, "test.geoh5")
    uijson_path = geoh5_path.replace(".geoh5", ".ui.json")
    sweep_path = uijson_path.replace(".ui", "_sweep.ui")

    workspace = Workspace(geoh5_path)
    locs = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]])
    pts = Points.create(workspace, name="data", vertices=locs)
    dat = pts.add_data({"initial": {"values": np.ones(4, dtype=np.int32)}})
    ui_json = {
        "data_object": {
            "label": "Object",
            "meshType": "{202C5DB1-A56D-4004-9CAD-BAAFD8899406}",
            "value": pts,
        },
        "data": {
            "association": "Vertex",
            "dataType": "Integer",
            "label": "data",
            "parent": "data_object",
            "value": dat,
        },
        "param": {"label": "Add value", "value": 1},
    }
    ui_json = dict(ui_json, **deepcopy(default_ui_json))
    ui_json["geoh5"] = workspace
    ui_json["run_command"] = "sweeps.sample_worker"
    ifile = InputFile(
        ui_json=ui_json,
        data={k: v["value"] if isinstance(v, dict) else v for k, v in ui_json.items()},
    )
    ifile.write_ui_json("test.ui.json", path=tmp_path)

    @dataclass
    class ArgsStandin:
        file: None
        generate: None
        parameters: None

    args = ArgsStandin(file=uijson_path, generate=True, parameters=["param"])

    main(args)

    with open(sweep_path, encoding="utf-8") as file:
        uijson = json.load(file)

    uijson["param_end"]["value"] = 2
    uijson["param_end"]["enabled"] = True
    uijson["param_n"]["value"] = 2
    uijson["param_n"]["enabled"] = True

    with open(sweep_path, "w", encoding="utf-8") as file:
        json.dump(uijson, file, indent=4)

    args.file = sweep_path
    args.generate = False
    args.parameters = None

    workspace.close()
    main(args)
    workspace.open()

    with open(os.path.join(tmp_path, "lookup.json"), encoding="utf-8") as file:
        lookup = json.load(file)

    file_map = {v["param"]: k for k, v in lookup.items()}
    check = []
    for param in file_map:
        out_ws = Workspace(os.path.join(tmp_path, file_map[param] + ".ui.geoh5"))
        result = out_ws.get_entity("final")[0].values
        check.append(all(result == 1 + param))

    assert all(check)
