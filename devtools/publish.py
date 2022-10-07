#  Copyright (c) 2022 Mira Geoscience Ltd.
#
#  This file is part of param-sweeps.
#
#  param-sweeps is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  param-sweeps is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with param-sweeps.  If not, see <https://www.gnu.org/licenses/>.

from pathlib import Path

from poetry_publish.publish import poetry_publish

import sweeps


def publish():
    poetry_publish(
        package_root=Path(sweeps.__file__).parent.parent,
        version=sweeps.__version__,
    )
