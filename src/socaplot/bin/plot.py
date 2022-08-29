# (C) Copyright 2022-2022 UCAR
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

import click
import pathlib
from pathlib import Path
import subprocess as sp
from itertools import product
import dateutil.parser as dtp
from glob import glob
import os

@click.command()
@click.argument('exp_dir',
    type=click.Path(exists=True, dir_okay=True),
    nargs=-1, required=True,)
def plot(exp_dir):
    """ Plot one or more experiments.

    EXP_DIR should be the top level directory of an experiment, more than
    one experiment can be given.

    NOTE: the experiment directory must have the variable "EXP_NAME" added
    to the exp.config file.
    """

    exp_dir = [pathlib.Path(d).resolve() for d in exp_dir]

    # sanity checks on the input experiments
    if len(set(exp_dir)) < len(exp_dir):
        raise ValueError(
            'cannot use the same experiment more than once on'
            ' the command line.')
    for d in ('cycle_status','exp.config','obs_bin'):
        # make sure each listed exp directory has the required files/subdirectories
        for ed in exp_dir:
            if not (ed / d).exists():
                raise ValueError(
                    f'experiment at "{ed}" does not contain required "{d}"')

    # if a single experiment:
    if len(exp_dir) == 1:
        print('plotting all plots for a single experiment')
    else:
        print('plotting all plots for multiple experiments')

    # read in the per-experiment properties
    exp_param = {}
    for d in exp_dir:
        exp_config_file = d / 'exp.config'

        # read from exp.config
        try:

            # get the experiment name
            name = sp.check_output(f'. {exp_config_file} && echo $EXP_NAME', shell=True)
            name = name.decode().strip()
            if not len(name):
                raise ValueError(f'illegal value for EXP_NAME "{name}"')

            # get whether it is regional
            regional = sp.check_output(f'. {exp_config_file} && echo $DA_REGIONAL_ENABLED', shell=True)
            regional = regional.decode().strip()
            regional = True if regional in ('t','T','1', 'y', 'Y') else False

            # start date
            startdate = sp.check_output(f'. {exp_config_file} && date -u -d $EXP_START_DATE', shell=True)
            startdate = dtp.parse(startdate.decode().strip())
        except:
            raise RuntimeError(f'Unable to read variables from file "{exp_config_file}"')

        # read from cycle_status
        cycle_status_file = d / 'cycle_status'
        with open(cycle_status_file) as f:
            enddate = dtp.parse(f.read())

        if name in exp_param:
            raise ValueError(
                f'experiment name "{name} is already present. \n'
                f' trying to add: "{d}" \n'
                f' already present: "{exp_param[name]["path"]}"')

        exp_param[name] = {
            'path': d,
            'regional': regional,
            'startdate': startdate,
            'enddate': enddate
        }
    print('experiments: \n ', '\n  '.join(exp_param.keys()))

    # calculate the common time period across all experiments
    common_startdate = max([e['startdate'] for e in exp_param.values()])
    common_enddate = min([e['enddate'] for e in exp_param.values()])
    print(
        'generating plots for the common period of: \n'
        f'  startdate: {common_startdate} \n'
        f'  enddate: {common_enddate}')

    # generate / find the merged files
    # TODO remove these hardcoded values
    binning = 'hires_all'
    for exp, plat in product(exp_param.keys(), ('adt', 'sst' )):
        pfx='_'.join([d.strftime("%Y%m%d%H") for d in (common_startdate, common_enddate)])
        exp_file = exp_param[exp]['path'] / f'obs_bin/l1c/{binning}.{plat}.{pfx}.nc'

        # use bespin to merge the files
        if not exp_file.exists():
            print('creating merged file: ', exp_file)
            input_files = exp_param[exp]['path'] / f'obs_bin/l1b/????/*/{binning}.{plat}.nc'
            input_files = glob(str(input_files))
            input_files = sorted(list(filter(
                lambda f: common_startdate.strftime('%Y%m%d%H') <= Path(f).parts[-2] < common_enddate.strftime("%Y%m%d%H"),
                input_files)))

            if not exp_file.parent.exists():
                os.makedirs(exp_file.parent)

            cmd = f'bespin merge {" ".join(input_files)} -o  {exp_file}'
            sp.check_call(cmd, shell=True)

    # generate plots!
    print("Generating plots...")
    print("NOT YET IMPLEMENTED!")