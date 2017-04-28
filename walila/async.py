# -*- coding: utf-8 -*-

import logging
import functools

import celery

from celery import Task


logger = logging.getLogger(__name__)


class DefaultSettings(object):
    BROKER_URL = 'amqp://guest:guest@localhost:5672'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379'


class WalilaTask(Task):
    """Custom task class"""

    @classmethod
    def on_bound(cls, app):
        """Called when the task is bound to an app"""

    def on_success(self, retval, task_id, args, kwargs):
        logger.info("Task: %s done, result: %s", task_id, retval)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.info("Task: %s fail, reason: %s", task_id, exc)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """"""


def _bind_own_base_task(func):
    @functools.wraps(func)
    def _(*args, **kwargs):
        app = func(*args, **kwargs)
        setattr(app, 'Task', WalilaTask)
        return app
    return _


def init_celery_app(settings):
    """Init celery app with settings objec"""
    app = celery.Celery()
    app.config_from_object(settings)
    return app


# FIXME: register task first before run worker...
class TaskManager(object):

    def __init__(self, app_settings, app_initialize_func=None):
        self.app = None
        self.tasks = {}
        self.queues = {}
        self.async_result = {}

        if not app_initialize_func:
            app_initialize_func = init_celery_app

        self.app_initialize_func = app_initialize_func

        self.init_app(app_settings)

    def init_app(self, settings):
        if self.app is None:
            self.app = self.app_initialize_func(settings)

    def register_task(self, task_name, task, queue_name='default', **kwargs):
        """Reigster a task with `task_name` `task func` `queue_name` etc.
        """
        assert callable(task), "Task should be a function or method"
        wrapper_task = self.app.task(
            bind=True, base=WalilaTask, **kwargs)(task)
        self.tasks[task.__name__] = wrapper_task
        self.queues[task_name] = queue_name
        return True

    def apply_async(self, task_name, *args, **kwargs):
        task = self.tasks[task_name]
        queue = self.queues[task_name]
        async_result = task.si(*args, **kwargs).apply_async(queue=queue)
        self.async_result[task_name] = async_result
        return async_result

    # alias
    perform=apply_async

    def get_last_result(self, task_name):
        return self.async_result[task_name]

task_manager = TaskManager(DefaultSettings)
app = task_manager.app
