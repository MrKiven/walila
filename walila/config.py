# -*- coding: utf-8 -*-

import sys
import logging
import yaml

from .consts import (
    APP_CONFIG_PATH,
    DEFAULT_WORKER_CLASS,
    DEFAULT_WORKER_CONNECTIONS,
    DEFAULT_WORKER_TIMEOUT,
    DEFAULT_APP_PORT,
)
from .utils import cached_property, get_cpu_count

logger = logging.getLogger(__name__)


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
    def app_settings_uri(self):
        return self.config['settings']

    @cached_property
    def celery_settings(self):
        return self.config.get('celery_settings')

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

    def auto_worker_num(self):
        """http://docs.gunicorn.org/en/latest/design.html#how-many-workers"""
        return 2 * get_cpu_count() + 1

    def get_app_binds(self):
        return "0.0.0.0:%d" % self.port

    def get_app_n_workers(self):
        return self._get_conf('worker_nums', )

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
