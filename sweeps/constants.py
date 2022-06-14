defaults = {
    "title": "Parameter sweep",
    "run_command": "SweepDriver.run",
    "conda_environment": "sweeps",
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "geoh5": None,
    "worker_uijson":  None
}

default_ui_json = {
    "title": "Parameter sweep",
    "run_command": "SweepDriver.run",
    "conda_environment": "sweeps",
    "monitoring_directory": None,
    "workspace_geoh5": None,
    "geoh5": None,
    "worker_uijson": {
        "main": True,
        "label": "Worker ui.json file",
        "value": None
    }
}
