# -*- coding: utf-8 -*-

"""
  Walila - Awesome toolkit
"""

import yaml
import ConfigParser

from .const import (
    DEFAULT_APP_CONFIG_PATH,
    DEFAULT_ENV,
    DEFAULT_ENV_KEY,
    DEFAULT_MAIN_SECTIONS,
    DEBUG,
    DEFAULT_MSG_CONFIG_PATH,
)
from .utils import cached_property


class AppConfig(object):

    def __init__(self):
        self._config = None
        self._env = DEFAULT_ENV
        self._current_env_configs = {}

    def load(self, config_path=DEFAULT_APP_CONFIG_PATH):
        self._config = ConfigParser.ConfigParser()
        self._config.read(config_path)
        return self

    @cached_property
    def env(self):
        return self._config.get(DEFAULT_MAIN_SECTIONS, DEFAULT_ENV_KEY)

    @cached_property
    def debug(self):
        return self._config.getboolean(DEFAULT_MAIN_SECTIONS, DEBUG)

    @cached_property
    def configs(self):
        if not self._current_env_configs:
            configs = self._config.items(self.env)
            for key, value in configs:
                self._current_env_configs[key] = value
        return self._current_env_configs

    def __getattr__(self, name):
        return self.configs.get(name)


# Singleton
app_config = None


def load_app_config(path=DEFAULT_APP_CONFIG_PATH):
    """load app config via given config path."""
    global app_config
    if app_config is None:
        app_config = AppConfig().load(config_path=path)
    return app_config


class MsgConfig(object):

    def __init__(self):
        self.config = None

    def load(self, path=DEFAULT_MSG_CONFIG_PATH):
        with open(path) as msg_fd:
            self.config = yaml.load(msg_fd)
        return self

    def __getattr__(self, name):
        return self.config.get(name)


msg_config = None


def load_msg_config(path=DEFAULT_MSG_CONFIG_PATH):
    global msg_config
    if msg_config is None:
        msg_config = MsgConfig().load(path=path)
    return msg_config
