# -*- coding: utf-8 -*-

import sys
import socket
import click

from ..config import load_env_config
from .utils import _validate_env


@click.command()
@click.argument("app", required=True)
@click.option("-q", "--queue-name", type=str, default="default",
              help="Queue to consume, should be defined in app.yaml")
@click.option("-w", "--nworkers", type=int, default=1,
              help="Number of workers")
@click.option("-p", "--process_num", type=int, default=1,
              help="Number of processes to run celery worker")
@click.option("--environment", type=str, default=load_env_config().env,
              help='current envionment', callback=+_validate_env)
def consume(app, queue_name, nworkers, process_num, environment):

    load_env_config().set_currnet_env(environment)

    def celery_worker():
        from celery.bin.celery import main
        from ..env import initialize

        initialize()

        hostname = socket.gethostname()

        argv = ["celery", "worker", "-l", "INFO", "-A", app,
                "-c", str(nworkers), "-Q", queue_name, "-E",
                "-n", "%s@%s" % (queue_name, hostname), "--without-heartbeat",
                "--without-gossip", "--without-mingle"]
        main(argv)

    sys.exit(celery_worker())
