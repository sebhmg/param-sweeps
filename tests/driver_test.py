#  Copyright (c) 2022 Mira Geoscience Ltd.
#
#  This file is part of param-sweeps.
#
#  param-sweeps is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

import os
import json
from copy import deepcopy

from geoh5py.workspace import Workspace
from sweeps.driver import generate
from sweeps.constants import default_ui_json

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
    test["worker_uijson"]["value"] = ws.h5file.replace("ui.geoh5", "ui.json")

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