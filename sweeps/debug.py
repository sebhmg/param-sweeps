from geoh5py.ui_json import InputFile

from params import SweepParams
from driver import SweepDriver

path = "C:/Users/Benjamink/OneDrive - Mira Geoscience Limited/Documents/test/test_sweep/plate_modelling_sweep.ui.json"
ifile = InputFile.read_ui_json(path)
params = SweepParams(ifile)
SweepDriver(params).run()

# from driver import generate
# path = "../../../test/test_plate_modelling.ui.json"
# generate(path)