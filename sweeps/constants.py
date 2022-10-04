#  Copyright (c) 2022 Mira Geoscience Ltd.
#
#  This file is part of param-sweeps.
#
#  param-sweeps is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

defaults = {
    "title": "Parameter sweep",
    "run_command": "sweeps.driver",
    "conda_environment": "sweeps",
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "geoh5": None,
}

default_ui_json = {
    "title": "Parameter sweep",
    "run_command": "SweepDriver.run",
    "conda_environment": "sweeps",
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "geoh5": None,
}
