# -*- coding: utf-8 -*-

from ..async import task_manager

app = task_manager.app


def add(self, x, y):
    return x + y

task_manager.register_task(add)
# result = task_manager.apply_async('Add', 1, 2)
