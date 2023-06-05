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
import pytz

@click.command()
@click.argument('exp_dir',
    type=click.Path(exists=True, dir_okay=True),
    nargs=-1, required=True,)
@click.option('-s', '--startdate', help=(
    "start date to use for plots. Default is to use the earliest date"
    " among all the experiments."))
@click.option('-e', '--enddate', help=(
    "end date to use for the plots. Default is to use the earliest date"
    " amon all the experiments."))
@click.option('-o', '--outdir', help=(
    "output path in which to store the plots."),
    type=click.Path(dir_okay=True),
    default='./plots', show_default=True)
def plot(exp_dir, startdate, enddate, outdir):
    """ Plot one or more experiments.

    EXP_DIR should be the top level directory of an experiment, more than
    one experiment can be given.

    NOTE: the experiment directory must have the variable "EXP_NAME" added
    to the exp.config file.
    """

    #parse input args
    exp_dir = [pathlib.Path(d).resolve() for d in exp_dir]
    outdir = pathlib.Path(outdir).resolve()
    if startdate is not None:
        startdate = pytz.utc.localize(dtp.parse(startdate))
    if enddate is not None:
        enddate = pytz.utc.localize(dtp.parse(enddate))

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
            exp_name = sp.check_output(f'. {exp_config_file} && echo $EXP_NAME', shell=True)
            exp_name = exp_name.decode().strip()
            if not len(exp_name):
                raise ValueError(f'illegal value for EXP_NAME "{exp_name}"')

            # get whether it is regional
            exp_regional = sp.check_output(f'. {exp_config_file} && echo $DA_REGIONAL_ENABLED', shell=True)
            exp_regional = exp_regional.decode().strip()
            exp_regional = True if exp_regional in ('t','T','1', 'y', 'Y') else False

            # start date
            exp_startdate = sp.check_output(f'. {exp_config_file} && date -u -d $EXP_START_DATE', shell=True)
            exp_startdate = dtp.parse(exp_startdate.decode().strip())
        except:
            raise RuntimeError(f'Unable to read variables from file "{exp_config_file}"')

        # read from cycle_status
        cycle_status_file = d / 'cycle_status'
        with open(cycle_status_file) as f:
            exp_enddate = dtp.parse(f.read())

        if exp_name in exp_param:
            raise ValueError(
                f'experiment name "{exp_name} is already present. \n'
                f' trying to add: "{d}" \n'
                f' already present: "{exp_param[exp_name]["path"]}"')

        exp_param[exp_name] = {
            'path': d,
            'regional': exp_regional,
            'startdate': exp_startdate,
            'enddate': exp_enddate
        }
    print('experiments: \n ', '\n  '.join(exp_param.keys()))

    # calculate the common time period across all experiments
    common_startdate = max([e['startdate'] for e in exp_param.values()])
    common_enddate = min([e['enddate'] for e in exp_param.values()])
    if startdate is None:
        startdate = common_startdate
    if enddate is None:
        enddate = common_enddate
    if startdate < common_startdate:
        raise ValueError(
            f'given startdate "{startdate}" is outside the range of the'
            f' common start dates for the experiments "{common_startdate}')
    if enddate > common_enddate or enddate < startdate:
        raise ValueError(
            f'given startdate "{enddate}" is outside the range of the'
            f' common end dates for the experiments "{common_enddate}')
    print(
        'generating plots for the common period of: \n'
        f'  startdate: {startdate} \n'
        f'  enddate: {enddate}')

    # ---------------------------------------------------------------------------------------------
    # generate / find the merged files
    # ---------------------------------------------------------------------------------------------
    # TODO remove these hardcoded values
    binning = 'hires_all'
    date_pfx='_'.join([d.strftime("%Y%m%d%H") for d in (startdate, enddate)])
    for exp, plat in product(exp_param.keys(), ('adt', 'sst', 'sss' )):        
        exp_file = exp_param[exp]['path'] / f'obs_bin/l1c/{binning}.{plat}.{date_pfx}.nc'

        # use bespin to merge the files
        if not exp_file.exists():
            input_files = exp_param[exp]['path'] / f'obs_bin/l1b/????/*/{binning}.{plat}.nc'
            input_files = glob(str(input_files))
            input_files = sorted(list(filter(
                lambda f: startdate.strftime('%Y%m%d%H') <= Path(f).parts[-2] < enddate.strftime("%Y%m%d%H"),
                input_files)))

            # skip if there are no files to merges
            if len(input_files) < 2: # TODO, handle case where len == 1?
                continue

            print('creating merged file: ', exp_file)
            if not exp_file.parent.exists():
                os.makedirs(exp_file.parent)
            cmd = f'bespin merge {" ".join(input_files)} -o  {exp_file}'
            sp.check_call(cmd, shell=True)


    # ---------------------------------------------------------------------------------------------
    # generate plots!
    # ---------------------------------------------------------------------------------------------
    print("Generating plots...")
    print(f" saving to {outdir}")

    # plot name
    if len(exp_param.keys()) == 1:
        # "exp"
        exp = list(exp_param.keys())[0]
        exp_name = f'{exp}'
        outdir = outdir / exp_name
    elif len(exp_param.keys()) == 2:
        # "exp2 - exp1"        
        exp1, exp2 = list(exp_param.keys())
        exp_name = f'{exp2}-{exp1}'
        outdir = outdir / exp_name
    else:
        raise NotImplementedError("Have not implemented plotting for >2 experiments")
        
    # for each obs platform type:
    # TODO remove hardcoded values here
    binning = 'hires_all'    
    for plat in ('adt', 'sst', 'sss'):
        print(f'Platform: {plat}')
        infiles = []
        for exp in exp_param.keys():
            infile = exp_param[exp]['path'] / 'obs_bin' / 'l1c' 
            infile = infile / f'{binning}.{plat}.{date_pfx}.nc'
            if infile.exists():
                infiles.append(infile)
        
        # skip if there are no valid files
        if len(infiles) != len(exp_param):
            continue

        # plot everything twice. Once with all obs, once with only obs that pass qc
        # TODO remove hardcoded use of hat10        
        for qc in ('', '_qc'):
            # create output directory
            plat_outdir = outdir / (plat + qc)
            if not plat_outdir.exists():
                os.makedirs(plat_outdir)

            # select which qc to apply
            if qc == '':
                args = '-c qc'
            else:
                args = '-s qc:0'
            
            if len(infiles) > 1:
                args = f'{args} --diff'

            infiles_str = ' '.join([str(s) for s in infiles])
            cmd = f'padme autoplot --domain hat10 -o {plat_outdir}/{exp_name} {infiles_str} {args}'
            sp.check_call(cmd, shell=True)

    