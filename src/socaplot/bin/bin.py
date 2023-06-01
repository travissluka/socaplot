# (C) Copyright 2022-2022 UCAR
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

import shutil
import click
import os
from glob import glob
import pathlib
import subprocess as sp
from datetime import datetime
import dateutil.parser as dtp
import socaplot.config as configs


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

    WARNING: things are currently hardcoded for the regional HAT10 domain.
    If this is not what you are using, turn back now (or talk to Travis).
    """

    # parse input dates
    startdate = datetime(1,1,1,0) if startdate is None else dtp.parse(startdate)
    enddate = datetime(9999,1,1) if enddate is None else dtp.parse(enddate)

    # input / output directories
    exp_dir = pathlib.Path(exp_dir).resolve()
    in_dir = exp_dir / 'obs_out'
    out_dir = exp_dir / 'obs_bin'

    #-----------------------------------------------------------------------------------------------
    ### l1a and l1b binning (binning within a single cycle date)
    #-----------------------------------------------------------------------------------------------
    # determine if I should look in ens or ctrl dir, not both (for now)
    # TODO, handle both directories when we start doing envar experiments
    ctrl_files=sorted(glob(f'{in_dir}/????/??????????/ctrl/{obstype}.nc'))
    ens_files=sorted(glob(f'{in_dir}/????/??????????/ens/{obstype}.nc'))
    obs_files=ctrl_files if len(ctrl_files) >= len(ens_files) else ens_files
    print(f"processing {len(obs_files)} files")

    # for each directory that contains observations
    obs_dirs=sorted(list(set([pathlib.Path(f).parent for f in obs_files])))
    for obs_dir in obs_dirs:

        # skip dates outside the desired range
        dt=pathlib.Path(obs_dir).parts[-2]
        cdate=dtp.parse(f'{dt[:8]}T{dt[8:10]}')
        if cdate > enddate or cdate < startdate:
            continue

        # l1a binning, for each input file
        #-------------------------------------------------------------------------------------------
        for in_file in sorted(glob(f'{obs_dir}/{obstype}.nc')):
            in_file = pathlib.Path(in_file)
            pfx = in_file.parts[-1].split('.')[0]
            ot = pfx.split('_')[0]
            for l1a_cfg in configs.l1a:
                config = configs.l1a[l1a_cfg]
                out_file = out_dir / 'l1a' / dt[:4] / dt/ f'{l1a_cfg}.{pfx}.nc'

                # skip if file already exists?
                # TODO also check if binning spec has changed
                opts = ''
                if out_file.exists():
                    if not force and out_file.stat().st_mtime > in_file.stat().st_mtime:
                        continue
                    else:
                        opts += ' -O'

                # skip if yaml tells us to skip
                skip = False
                if 'skip' in config['obs types'][ot]:
                    skip = config['obs types'][ot]['skip']
                if skip:
                    continue

                # create output directory if not already existing
                if not out_file.parent.exists():
                    os.makedirs(out_file.parent)


                print(f'l1a "{l1a_cfg}" processing for {out_file}')
                cmd = f'bespin bin {in_file} -o {out_file}'
                cmd+=' '.join([f' -d {d}' for d in config['diagnostics']])
                cmd+=' '.join([f' -f {f}' for f in config['filters']])
                cmd+=' '.join([f' -b {b}' for b in config['bins']])
                cmd+=f' -v {config["obs types"][ot]["variable"]}'
                cmd+=opts
                sp.check_call(cmd, shell=True)

        # l1b binning, merging multiple types within a single cycle
        #-------------------------------------------------------------------------------------------
        # TODO generalize this and move into config files
        # also, this is a bit of a mess
        for l1b_cfg in configs.l1b:
            config = configs.l1b[l1b_cfg]
            assert config['operation']['name'] == 'merge_plat'
            src_lvl = config['source']['level']
            src_name = config['source']['name']
            in_dir = out_dir / src_lvl / dt[:4] / dt
            obs_types = set([
                f.split('/')[-1].split('.')[1].split('_')[0]
                for f in glob(str(in_dir / f'{src_name}.{obstype}.nc'))])
            for ob_type in obs_types:
                try:
                    skip_plats = config['operation']['ignore'][ob_type]
                except:
                    skip_plats = []
                in_files = glob(str(in_dir / f'{src_name}.{ob_type}_*.nc'))
                in_files = [
                    f for f in in_files
                    if '_'.join(f.split('/')[-1].split('.')[1].split('_')[1:]) not in skip_plats]
                out_file = out_dir / 'l1b' / dt[:4] / dt / f'{l1b_cfg}.{ob_type}.nc'

                # skip if file already exists?
                opts = ''
                if out_file.exists():
                    invalid = any([pathlib.Path(f).stat().st_mtime > out_file.stat().st_mtime for f in in_files])
                    if not invalid and not force:
                        continue
                    else:
                        opts += ' -O'

                # create output directory if not already existing
                if not out_file.parent.exists():
                    os.makedirs(out_file.parent)

                print(f'l1b "{l1b_cfg}" processing for {out_file}')
                if len(in_files) > 1:
                    cmd = f'bespin merge {" ".join(in_files)} -o {out_file}'
                    cmd+=opts
                    sp.check_call(cmd, shell=True)
                else:
                    # TODO should i symlink instead?
                    shutil.copy(in_files[0], out_file)

    #-----------------------------------------------------------------------------------------------
    ### l1c binning (across cycle dates)
    #-----------------------------------------------------------------------------------------------
