#  Copyright (c) 2022 Mira Geoscience Ltd.
#
#  This file is part of param-sweeps.
#
#  param-sweeps is distributed under the terms and conditions of the MIT License
#  (see LICENSE file at the root of this source code package).
import sys

from geoh5py.ui_json import InputFile


def run(ifile):

    with ifile.workspace.open(mode="r+"):
        result = ifile.data["data"].values + ifile.data["param"]
        ifile.data["data_object"].add_data({"final": {"values": result}})


if __name__ == "__main__":
    filepath = sys.argv[1]
    input_file = InputFile.read_ui_json(filepath)
    run(input_file)
