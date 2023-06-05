# `socaplot` plotting tools
testbed for `soca-science` plotting using ~~JCSDA's~~ Travis's [BESPIN](https://github.com/travissluka/bespin) and [PADME](https://github.com/travisslukla/padme) packages

## Installation

(note these instructions will change once the branches have stabilized and can be pulled directly by pip)

### 1. Get source code

``` console
> mkdir socaplot
> cd socaplot
> git clone git@github.com:travissluka/bespin.git --branch feature/soca
> git clone git@github.com:travissluka/padme.git --branch feature/soca
> git clone git@github.com:travissluka/socaplot.git
```

### 2. Install conda

Conda is preferable to setting up a python venv because some libraries such as GEOS are required, and are easier to get via conda if they are not already available on the machine. If you already have a conda environment installed that you want to use, you can skip this section

```console
> wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
> console Miniconda3-latest-Linux-x86_64.sh
(install to ./conda when asked)
> source conda/bin/activate
```

### 3. Create `socaplot` conda environment

This will create a conda environment named `socaplot` with all the required dependencies

```console
> conda env create -f socaplot/environment.yaml
```

### 4. Activate the conda environment

Now, and everytime you open a new bash instance to run `socaplot` tools, you'll have to run:

```console
> source conda/bin/activate socaplot
```

### 5. Install the plotting packages

The packages are installed in "editable" mode, meaning if you need to update a version of any given package you can simply do a `git pull` without having to re-install.

```console
> pip install -e bespin
> pip install -e padme
> pip install -e socaplot
```

## Usage

### 1. Binning

For each experiment you want to plot, simply run:

```console
> socaplot bin <path_to_exp>
```

and the binned O-B stats will be calculated for each observation type and each cycle.

Note: the `exp.config` file for the experiment needs to contain the variable `EXP_NAME`, it is suggested that you make this short, and unique, because it will be used later by the plotting tool for filenames and legends.

For detailed usage of the `bin` tool, run:

```console
> socaplot bin --help
```

### 2. Plotting

> NOTE: The plotting is currently hardcoded for the HAT10 regional domain!
 
> NOTE: Only 2D spatial plots are currently working, timeseries will be added soon(ish)

The plotting tool will automatically plot all available plots for the time period available for either 1) a single experiment, or 2) a comparison of 2 or more different experiments. The types of plots generated will depend on the number of experiments given.

For example, to generate comparison plots of `exp2 - exp1` (note that the first experiment listed on the command line should be considered the "reference" experiment that is subtracted from the other(s) ), run:

```console
> socaplot plot <exp1> <exp2>
```

The script will first merge the input binned files for the given timeperiod, if not already done so, then generate a whole bunch of plots.


If you have multiple experiments that you plan on separately comparing, and there is a chance that they have different end dates that they have run to, it is recommended that you used the `-e <enddate>` option when plotting so that all 2D spatial plots use the same date.

For detailed usage of the `plot` tool, run:

```console
> socaplot plot --help
```