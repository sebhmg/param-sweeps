#  Copyright (c) 2022 Mira Geoscience Ltd.
#
#  This file is part of param-sweeps.
#
#  param-sweeps is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

from copy import deepcopy
import numpy as np
from geoh5py.ui_json import InputFile
from geoh5py.workspace import Workspace
from sweeps.base import BaseParams
from sweeps.constants import default_ui_json
from sweeps.constants import defaults

class SweepParams(BaseParams):

    def __init__(self, input_file=None, **kwargs):
        self._default_ui_json = deepcopy(default_ui_json)
        self._defaults = deepcopy(defaults)
        self._worker_uijson = None

        if input_file is None:
            ui_json = deepcopy(self._default_ui_json)
            input_file = InputFile(
                ui_json=ui_json,
                validations=self.validations,
                validation_options={"disabled": True},
            )

        super().__init__(input_file=input_file, **kwargs)


    @property
    def worker_uijson(self):
        return self._worker_uijson

    @worker_uijson.setter
    def worker_uijson(self, val):
        self._worker_uijson = val

    @property
    def geoh5(self):
        return self._geoh5

    @geoh5.setter
    def geoh5(self, val):
        if val is None:
            self._geoh5 = val
            return
        self.setter_validator(
            "geoh5", val, fun=lambda x: Workspace(x) if isinstance(val, str) else x
        )
        self.worker_uijson = val.h5file.replace(".ui.geoh5", ".ui.json")
        if self.input_file.workspace is None:
            self.input_file.workspace = self.geoh5

    def worker_parameters(self):
        return [k.replace("_start", "") for k in self.__dict__ if k.endswith("_start")]

    def parameter_sets(self):
        names = self.worker_parameters()
        sets = {n: (getattr(self, f"{n}_start"), getattr(self, f"{n}_end"), getattr(self, f"{n}_n")) for n in names}
        sets = {k: [v[0]] if v[1] is None else np.linspace(*v, dtype=int).tolist() for k, v in sets.items()}
        return sets



