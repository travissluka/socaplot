# (C) Copyright 2022-2022 UCAR
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

import click

from .bin import bin_
from .plot import plot

@click.group()
@click.version_option()
def cli():
    """soca-science plotting tools using BESPIN/PADME packages.

        Joint Center for Satellite Data Assimilation (JCSDA) ©2022
    """
    pass

cli.add_command(bin_)
cli.add_command(plot)