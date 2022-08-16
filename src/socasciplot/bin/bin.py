# (C) Copyright 2022-2022 UCAR
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

import click
from glob import glob
import os
import pathlib
import subprocess as sp
import yaml
from datetime import datetime
import dateutil.parser as dtp

# load binning specification
# TODO allow user to manually specify this?
def load_config():
    config_file='../../../binning_specs/binning.yaml'
    config_file=(pathlib.Path(__file__).parent / config_file).resolve()
    config=yaml.safe_load(open(str(config_file)))
    return config
config = load_config()


@click.command(name='bin')
@click.argument('exp_dir',
    type=click.Path(exists=True, dir_okay=True),
    required=True)
@click.option('-f', '--force',
    is_flag=True,
    help="force rebinning of all observations")
@click.option('-s', '--startdate')
@click.option('-e', '--enddate')
@click.option('-o', '--obstype', default="*")
def bin_(exp_dir, startdate, enddate, obstype, force):
    """Perform the initial raw binning on a single experiment.

    A single EXP_DIR pointing to the top level directory of a soca-science
    experiment.
    """

    # parse input dates
    if startdate is None:
        startdate = datetime(1,1,1,0)
    else:
        startdate = dtp.parse(startdate)

    if enddate is None:
        enddate = datetime(9999,1,1)
    else:
        enddate = dtp.parse(enddate)


    # input / output directories
    exp_dir = pathlib.Path(exp_dir).absolute()
    in_dir = exp_dir / 'obs_out'
    out_dir = exp_dir / 'obs_bin/L1a'
    print(f'binning observations in: {in_dir}')
    assert in_dir.exists()

    # make output directory
    if not out_dir.exists():
        os.makedirs(out_dir)

    # for each directory that contains observations
    # TODO look at the ens directory also? for now I'll just look at ctrl
    obs_files=sorted(glob(f'{in_dir}/????/??????????/ctrl/{obstype}.nc'))
    obs_dirs=sorted(list(set([pathlib.Path(f).parent for f in obs_files])))
    print(f'processing {len(obs_files)} input files')
    for obs_dir in obs_dirs:
        dt=pathlib.Path(obs_dir).parts[-2]
        cdate=dtp.parse(f'{dt[:8]}T{dt[8:10]}')
        if cdate > enddate or cdate < startdate:
            continue

        print("")
        print(f'processing files in {obs_dir}')
        obs_files = sorted(glob(f'{obs_dir}/{obstype}.nc'))

        # make output dir if doesnt already exist
        obs_out_dir = out_dir / dt[0:4] / dt
        if not obs_out_dir.exists():
            os.makedirs(obs_out_dir)

        # bin input files
        for obs_file in obs_files:
            # determine the output path given the input path
            obs_t, obs_p = pathlib.Path(obs_file).parts[-1].split('.')[0].split('_')
            bin_file(obs_file, obs_out_dir, obs_t, obs_p)

        # merge files for a given dates
        obs_types = set([f.split('/')[-1].split('_')[0] for f in glob(f'{obs_dir}/*.nc')])
        for ob_type in obs_types:
            # remove obs files that are blacklisted via "skip merge"
            try:
                skip_plats=config['obs types'][ob_type]['skip merge']
            except:
                skip_plats=[]
            files=glob(f'{obs_out_dir}/*.{ob_type}.*.nc')
            files=[f for f in files if f.split('.')[-2] not in skip_plats]

            if not len(files) >1:
                continue

            merge_obs_types(files, obs_out_dir)


def bin_file(in_file, out_dir, obs_type, obs_plat):
    """Do all the desired binning on a single input file."""

    bin_name='binned'
    out_file = pathlib.Path(f'{out_dir}/{bin_name}.{obs_type}.{obs_plat}.nc')

    # if output file already exists, skip (unless force is set)
    # TODO use force flag
    if out_file.exists():
        print(f'skipping {out_file}')
        return

    # TODO these will change depending on what type of exp was run
    obs_type_config=config['obs types'][obs_type]

    # form the command line
    cmd=f'bespin bin {in_file} -o {out_file}'
    cmd+=' '.join([f' -d {d}' for d in config['diagnostics']])
    cmd+=' '.join([f' -f {f}' for f in config['filters']])
    cmd+=' '.join([f' -b {b}' for b in config['bins']])
    cmd+=f' -v {obs_type_config["variable"]}'

    # run it!
    sp.check_call(cmd, shell=True)


def merge_obs_types(in_files, out_dir):
    # determine the output filename
    out_pfx='.'.join(in_files[0].split('/')[-1].split('.')[-4:-2])
    out_file=f'{out_dir}/{out_pfx}.nc'

    # if output file already exists skip, unless force is set
    # TODO use force flag
    # TODO check to make sure input files have not changed
    if pathlib.Path(out_file).exists():
        return

    print(f'merging for {out_file}')
    # run the command
    cmd=f'bespin merge {" ".join(in_files)} -o {out_file}'
    sp.check_call(cmd, shell=True)
