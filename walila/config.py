# -*- coding: utf-8 -*-

import os
import sys
import logging
import yaml

from .consts import (
    APP_CONFIG_PATH,
    DEFAULT_WORKER_CLASS,
    DEFAULT_WORKER_CONNECTIONS,
    DEFAULT_WORKER_TIMEOUT,
    DEFAULT_APP_PORT,
    DEFAULT_ENV_CONFIG_PATH,
    DEFAULT_ENV,
    DEFAULT_LOG_PATH,
    DEFAULT_WORKER_NUM,
)
from .utils import cached_property, get_cpu_count

logger = logging.getLogger(__name__)


class EnvConfig(object):
    """Application independent config, as a yaml file at
    `/etc/southpay/env.yaml`. e.g:

        env: dev|testing|prod
        may_be_other_property: not usage yet
    """

    def __init__(self):
        self.config = None

    def load(self):
        try:
            with open(DEFAULT_ENV_CONFIG_PATH) as config_fd:
                self.config = yaml.load(config_fd)
        except(IOError, yaml.error.YAMLError):
            logger.error("Connot load env config %s, default `dev`",
                         DEFAULT_ENV_CONFIG_PATH)
            self.config = {}
        return self

    @property
    def env(self):
        return self.config.get('env', DEFAULT_ENV)

    def set_currnet_env(self, env):
        self.config.update({'env': env})


env_config = None


def load_env_config():
    """load env config lazily but only once"""
    global env_config
    if env_config is None:
        env_config = EnvConfig().load()
    return env_config


class AppConfig(object):
    """Application configs, as a yaml file at `APP_CONFIG_PATH`, e.g.:

        app_name: SouthPay
        settings: southpay.settings
        services:
            app: southpay.app:app
            worker_class: tornado
            requirements: requirements.txt
        celery_settings: celerysettings
    """

    def __init__(self):
        self.config = None

    def load(self, config_path=APP_CONFIG_PATH, raise_exc=False):
        try:
            with open(config_path) as config_fd:
                self.config = yaml.load(config_fd)
        except (IOError, yaml.error.YAMLError):
            if raise_exc:
                raise
            logger.error("Cannot load %s, exit.", config_path)
            sys.exit(1)
        return self

    @cached_property
    def app_name(self):
        return self.config['app_name']

    @cached_property
    def logger_name(self):
        """logger name for current application"""
        return self.config.get('logger_name', self.app_name)

    @cached_property
    def log_path(self):
        """log file path, exclude log file name, default: ``/tmp/``."""
        return self.config.get('log_path', DEFAULT_LOG_PATH)

    @cached_property
    def log_file_prefix(self):
        """`southpay`"""
        return self.app_name.lower()

    @cached_property
    def app_log_path(self):
        """app log path, e.g. /tmp/southpay.log"""
        return os.path.join(
            self.log_path,
            ".".join((self.log_file_prefix, 'log'))
        )

    @cached_property
    def task_log_path(self):
        """celery worker log path, e.g. /tmp/southpay_worker.log"""
        return os.path.join(
            self.log_path,
            "_".join((self.log_file_prefix, "worker.log"))
        )

    @cached_property
    def app_settings_uri(self):
        return "_".join((self.config['settings'], load_env_config().env))

    @cached_property
    def celery_settings(self):
        return "_".join((
            self.config.get('celery_settings', ''), load_env_config().env))

    @cached_property
    def app_self_config(self):
        """WSGI App instance config uri"""
        return "_".join((self.config['app_config'], load_env_config().env))

    @cached_property
    def async_queues(self):
        """Queues to consume"""
        return self.config.get('async_queues', 'default')

    @cached_property
    def worker_class(self):
        return self._get_conf('worker_class', DEFAULT_WORKER_CLASS)

    @cached_property
    def worker_connections(self):
        return self._get_conf(
            'worker_connections',
            DEFAULT_WORKER_CONNECTIONS)

    @cached_property
    def timeout(self):
        """Workers silent for more than this many seconds are killed and
           restarted.
        """
        return self._get_conf('timeout', DEFAULT_WORKER_TIMEOUT)

    @cached_property
    def port(self):
        return self._get_conf('port', DEFAULT_APP_PORT)

    @cached_property
    def app_uri(self):
        app = self._get_conf('app', None)
        if app is None:
            raise RuntimeError("Missing `app` in app.yaml.")
        return app

    @cached_property
    def auto_worker_num(self):
        """http://docs.gunicorn.org/en/latest/design.html#how-many-workers"""
        return 2 * get_cpu_count() + 1

    def get_app_binds(self):
        return "0.0.0.0:%d" % self.port

    def get_app_n_workers(self):
        from .env import is_in_dev
        if is_in_dev():
            return DEFAULT_WORKER_NUM
        return self._get_conf('worker_nums', self.auto_worker_num)

    def _get_conf(self, key, default):
        if 'services' in self.config:
            return self.config['services'].get(key, default)
        return self.config.get(key, default)


app_config = None


def load_app_config(raise_exc=False):
    """Load app config lazily but only once"""
    global app_config
    if app_config is None:
        app_config = AppConfig().load(raise_exc=raise_exc)
    return app_config
