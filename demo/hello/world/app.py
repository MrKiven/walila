# -*- coding: utf-8 -*-

import logging

from flask import Flask

from .tasks import task_manager

logger = logging.getLogger(__name__)

app = Flask(__name__)


def hello():
    return 'Hello world!\n'

@app.route('/tasks/<task_name>')
def send_task(task_name):
    if task_name not in task_manager:
        msg = "%r task not exists, skippping." % task_name
        logger.error(msg)
        return msg
    task_manager.perform(task_name)
    return 'Send Success!'

app.add_url_rule('/hello', 'hello', hello)
