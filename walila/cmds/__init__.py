# -*- coding: utf-8 -*-

import click

from .serve import serve


@click.group()
@click.version_option()
def walila():
    """Walila command line entry point"""


walila.add_command(serve)
