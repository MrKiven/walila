# -*- coding: utf-8 -*-

import sys
import logging
import yaml

from .consts import APP_CONFIG_PATH
from .utils import cached_property

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


app_config = None


def load_app_config(raise_exc=False):
    """Load app config lazily but only once"""
    global app_config
    if app_config is None:
        app_config = AppConfig().load(raise_exc=raise_exc)
    return app_config
