# -*- coding: utf-8 -*-

import sys
import socket
import click


@click.command()
@click.argument("app", required=True)
@click.option("-q", "--queue-name", type=str, default="default",
              help="Queue to consume, should be defined in app.yaml")
@click.option("-w", "--nworkers", type=int, default=1,
              help="Number of workers")
@click.option("-p", "--process_num", type=int, default=1,
              help="Number of processes to run celery worker")
def consume(app, queue_name, nworkers, process_num):

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
