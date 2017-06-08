# -*- coding: utf-8 -*-

import functools
import inspect

import celery

from celery import Task
from celery.utils.log import get_task_logger

from ..settings import settings
from ..config import load_app_config


logger = get_task_logger(__name__)


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


def init_celery_app():
    """Init celery app with settings objec.

    The transport part is the broker implementation to use, and the default is
    amqp, (uses librabbitmq if installed or falls back to pyamqp).
    """
    app = celery.Celery()
    app.conf.task_protocol = 1  # librabbitmq, no cover
    celery_config = load_app_config().celery_settings
    if settings.ASYNC_ENABLED:
        if not celery_config:
            raise RuntimeError("No celery configured!!")
        app.config_from_object(celery_config)
        return app


class TaskManager(object):
    """Async task manager (singleton)

    :param celery_settings: `walila.settings.settings.celeryconfig`
    :param app_initialize_func: initialize celery app,
     default `init_celery_app`

    Feature:

        * register async task
        * invoke async task
        * get async task's result(:class: `celery.result.AsyncResult`), option
        * tasks queues record

    Usage:

        # async_tasks.py

        from walila.async import task_manager
        from walila.async import app  # noqa

        def task_add(self, x, y):
            return x + y

        task_manager.register_task(task_add)



        # Start celery worker:

        $ celery -A your.pkg.async_task worker --loglevel=info -E -Q default

    """

    def __init__(self, app_initialize_func=None):
        self.app = None
        self.tasks = {}
        self.queues = {}
        self.async_result = {}

        if not app_initialize_func:
            app_initialize_func = init_celery_app

        self.app_initialize_func = app_initialize_func
        self.init_app()

    @property
    def celery_app(self):
        """Alias"""
        return self.app

    def init_app(self):
        if self.app is None:
            self.app = self.app_initialize_func()
        if self.app is None:
            raise RuntimeError("Celery is not enabled, check your settings.")

    def is_bind(self, task):
        args = inspect.getargspec(task)
        return args[0] and args[0][0] in ('self', 'cls')

    def register_task(self, task, task_name=None, queue_name='default',
                      base_task=WalilaTask, wrapper=None, **kwargs):
        """Reigster a task with `task_name` `task func` `queue_name` etc.
        """
        assert callable(task), "Task should be a function or method"
        support_queue_names = load_app_config().async_queues.split(',')
        if queue_name not in support_queue_names:
            raise RuntimeError(
                "Unsupport queue name: %r, check your `app.yaml`" % queue_name)
        wrapper_task = self.app.task(
            bind=self.is_bind(task), base=base_task, queue=queue_name,
            **kwargs)(task)
        if wrapper:
            wrapper_task = wrapper(wrapper_task)
        name = task_name or task.__name__
        self.tasks[name] = wrapper_task
        self.queues[name] = queue_name
        return True

    def apply_async(self, task_name, *args, **kwargs):
        task = self.tasks[task_name]
        queue = self.queues[task_name]
        async_result = task.si(*args, **kwargs).apply_async(queue=queue)
        self.async_result[task_name] = async_result
        return async_result

    def send_task(self, name):
        logger.warning("Not implemented yet.")

    # alias
    perform = apply_async

    def get_last_result(self, task_name):
        return self.async_result[task_name]

    def __contains__(self, task_name):
        return task_name in self.tasks


task_manager = TaskManager()
app = task_manager.celery_app
