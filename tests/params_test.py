#  Copyright (c) 2022 Mira Geoscience Ltd.
#
#  This file is part of param-sweeps.
#
#  param-sweeps is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

import os
import numpy as np
from copy import deepcopy
from geoh5py.workspace import Workspace
from geoh5py.ui_json import InputFile
from sweeps.params import SweepParams
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
    test["worker_uijson"]["value"] = ws.h5file.replace(".ui.geoh5", ".ui.json")
    ifile = InputFile(ui_json=test)
    params = SweepParams(ifile)

    assert params.worker_geoh5.h5file.split('\\')[-1] == "worker.ui.geoh5"
    worker_params = params.worker_parameters()
    assert len(worker_params) == 1
    assert worker_params[0] == "param1"
    psets = params.parameter_sets()
    assert len(psets) == 1
    assert "param1" in psets
    assert psets["param1"] == [1, 2]

