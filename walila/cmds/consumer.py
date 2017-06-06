# -*- coding: utf-8 -*-

import sys
import socket
import click

from ..config import load_env_config, load_app_config
from .utils import _validate_env


@click.command()
@click.argument("app", required=True)
@click.option("-w", "--nworkers", type=int, default=1,
              help="Number of workers")
@click.option("-p", "--process_num", type=int, default=1,
              help="Number of processes to run celery worker")
@click.option('--environment', type=str, default=load_env_config().env,
              help='current environment', callback=_validate_env)
def consume(app, nworkers, process_num, environment):

    load_env_config().set_currnet_env(environment)
    queue_names = load_app_config().async_queues

    def celery_worker():
        from celery.bin.celery import main
        from ..env import initialize, is_in_dev

        initialize()

        hostname = socket.gethostname()

        argv = ["celery", "worker", "-l", "INFO", "-A", app, "-B",
                "-c", str(nworkers), "-Q", queue_names, "-E",
                "-n", "%s@%s" % (queue_names, hostname), "--without-heartbeat",
                "--without-gossip", "--without-mingle"]
        if not is_in_dev():
            argv.extend(["-f", load_app_config().task_log_path])
        main(argv)

    sys.exit(celery_worker())
