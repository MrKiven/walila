# -*- coding: utf-8 -*-

from walila.queue.async import task_manager
from walila.queue.async import app  # noqa


def my_task(self):
    return 'hello world'

task_manager.register_task(my_task)
