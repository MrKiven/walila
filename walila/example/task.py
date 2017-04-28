# -*- coding: utf-8 -*-

from ..async import task_manager


def add(x, y):
    return x + y

task_manager.register_task('Add', add)
result = task_manager.apply_async('Add', 1, 2)
