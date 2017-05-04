# -*- coding: utf-8 -*-

from walila.queue.async import task_manager
from walila.queue.async import app  # noqa


def add(self, x, y):
    return x + y

task_manager.register_task(add)
# result = task_manager.apply_async('Add', 1, 2)
