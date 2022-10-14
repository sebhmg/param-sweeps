#  Copyright (c) 2022 Mira Geoscience Ltd.
#
#  This file is part of param-sweeps.
#
#  param-sweeps is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).

from pathlib import Path

from poetry_publish.publish import poetry_publish

import param_sweeps


def publish():
    poetry_publish(
        package_root=Path(param_sweeps.__file__).parent.parent,
        version=param_sweeps.__version__,
    )
