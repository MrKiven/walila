# -*- coding: utf-8 -*-

import click

from ..config import load_env_config
from .utils import _validate_env


@click.command(
    context_settings={
        "ignore_unknown_options": True,
        "allow_extra_args": True
    },
    add_help_option=True)
@click.option('--environment', type=str, default=load_env_config().env,
              help='current environment', callback=_validate_env)
@click.pass_context
def serve(ctx, environment):
    from ..runner import serve
    load_env_config().set_currnet_env(environment)

    group_name = ctx.parent.command.name + ' ' if ctx.parent else ''
    prog_name = "{}{}".format(group_name, ctx.command.name)

    import sys
    sys.argv = [prog_name] + ctx.args

    serve()


if __name__ == "__main__":
    # pylint: disable=E1120
    serve()
