# Param-sweeps

A Parameter sweeper for applications driven by ui.json files

This package contains two main modules.  One is for generating sweep
files, and the other is to run a sweep over some number of parameters
in a driver application.

### Basic Usage

To generate a sweep file from a ui.json file for an existing
application, use the following command:

```bash
conda activate param_sweeps && python -m param_sweeps.generate some_file.ui.json
```

This will create a new `some_file_sweep.ui.json` file that may be run
with:

```bash
python -m param_sweeps.driver some_file_sweep.ui.json
```

By default, this would execute a single run of the original parameters.
To design a sweep, simply drag the `some_file_sweep.ui.json` file into
the [Geoscience ANALYST Pro](https://mirageoscience.com/mining-industry-software/geoscience-analyst-pro/)
session that produced the original file and select start, end, and number
of samples values for parameters that you would like to sweep.


To organize the output, param-sweeps uses a `UUID` file naming scheme, with
a `lookup.json` file to map individual parameter sets back to their respective
files.
