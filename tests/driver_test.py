#  Copyright (c) 2022 Mira Geoscience Ltd.
#
#  This file is part of param-sweeps.
#
#  param-sweeps is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

import os
import json
import itertools
from copy import deepcopy

from geoh5py.workspace import Workspace
from geoh5py.ui_json import InputFile
from sweeps.driver import SweepParams, SweepDriver, sweep_forms, generate
from sweeps.constants import default_ui_json

def test_params(tmp_path):
    ws = Workspace(os.path.join(tmp_path, "worker.ui.geoh5"))
    test = deepcopy(default_ui_json)
    test.update(
        {
            "geoh5": ws.h5file,
            "param1_start": {
                "label": "param1 start",
                "value": 1
            },
            "param1_end": {
                "label": "param1 end",
                "value": 2
            },
            "param1_n": {
                "label": "param1 n samples",
                "value": 2
            },
        }
    )
    ifile = InputFile(ui_json=test)
    params = SweepParams.from_input_file(ifile)

    assert os.path.split(params.worker_uijson)[-1] == "worker.ui.json"
    worker_params = params.worker_parameters()
    assert len(worker_params) == 1
    assert worker_params[0] == "param1"
    psets = params.parameter_sets()
    assert len(psets) == 1
    assert "param1" in psets
    assert psets["param1"] == [1, 2]


def test_uuid_from_params():
    test = {"a": [1, 2], "b": [3, 4], "c": [5, 6]}
    iterations = list(itertools.product(*test.values()))
    for iter in iterations:
        trial_uuid = SweepDriver.uuid_from_params(iter)
        assert trial_uuid == SweepDriver.uuid_from_params(iter), "method is not deterministic"

def test_sweep_forms():
    forms = sweep_forms("test", 1)
    params = ["test_start", "test_end", "test_n"]
    assert len(forms) == 3
    assert all([k in forms for k in params])
    assert all([forms[k]["group"] == "Test" for k in params])
    assert all([f["value"] == 1 for f in forms.values()])
    assert forms["test_end"]["optional"]
    assert not forms["test_end"]["enabled"]
    assert forms["test_n"]["dependency"] == "test_end"
    assert forms["test_n"]["dependencyType"] == "enabled"
    assert not forms["test_n"]["enabled"]

def test_generate(tmp_path):
    ws = Workspace(os.path.join(tmp_path, "worker.ui.geoh5"))

    test = deepcopy(default_ui_json)
    test.update(
        {
            "geoh5": ws.h5file,
            "param1": {
                "label": "param1",
                "value": 1
            },
            "param2": {
                "label": "param2",
                "value": 2.5
            }
        }
    )

    path = os.path.join(tmp_path, "worker.ui.json")
    with open(path, 'w', encoding="utf8") as f:
        json.dump(test, f, indent=4)

    generate(path)
    with open(path.replace(".ui.json", "_sweep.ui.json"), 'r') as f:
        data = json.load(f)

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

    with open(path.replace(".ui.json", "_sweep.ui.json"), 'r') as f:
        data = json.load(f)

    assert "param2_start" not in data
    assert "param2_end" not in data
    assert "param2_n" not in data