# -*- coding: utf-8 -*-


def post_fork(server, worker):
    worker.app.chdir()
    from ..env import initialize
    # initialize worker process envrionment post fork before init_process
    initialize()
