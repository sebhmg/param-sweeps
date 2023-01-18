#  Copyright (c) 2023 Mira Geoscience Ltd.
#
#  This file is part of param-sweeps.
#
#  param-sweeps is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

default_ui_json = {
    "title": "Parameter sweep",
    "worker_uijson": None,
    "run_command": "param_sweeps.driver",
    "conda_environment": "param_sweeps",
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "geoh5": None,
}
