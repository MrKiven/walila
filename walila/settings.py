# -*- coding: utf-8 -*-

import logging

from importlib import import_module

from .utils import EmptyValue


logger = logging.getLogger(__name__)


class ConfigError(Exception):
    pass


class NotLoadedError(ConfigError):
    pass


def default_empty(val):
    """Make a legal default empty value"""
    return EmptyValue(val)


class BaseConfig(object):

    def __init__(self):
        self._settings = {}
        self._loaded = False

    def __getattr__(self, name):
        if not self._loaded:
            raise NotLoadedError("Error settings not loaded")
        if name not in self._settings:
            raise AttributeError(name)
        return self._settings[name]

    def __setattr__(self, name, value):
        if not self._is_legit_config_name(name):
            return object.__setattr__(self, name, value)
        if self._validate_config_attr(name, value):
            self._settings[name] = value

    def __iter__(self):
        return self._settings.__iter__()

    def _is_legit_config_name(self, name):
        """
        :rtype: bool
        """
        return name.isupper() and '__' not in name

    def _update_config(self, setting_obj, conf_to_update):
        for name in dir(setting_obj):
            if self._is_legit_config_name(name):
                setattr(self, name, getattr(setting_obj, name, None))
        if not self._loaded:
            self._loaded = True

        self._after_update_config()

    def _validate_config_name(self, name, value):
        return self._is_legit_config_name(name)

    def _validate_config_value(self, name, value, type=None):
        if EmptyValue.is_empty(value):
            return False
        if type is not None and issubclass(type, basestring):
            type = basestring
        if type is not None and not isinstance(value, type):
            return False
        return True

    def _validate_config_attr(self, name, value):
        return self._validate_config_name(name, value) and \
            self._validate_config_value(name, value)

    def _after_update_config(self):
        """Called after config update"""

    def from_object(self, obj):
        if isinstance(obj, basestring):
            settings_obj = import_module(obj)
        else:
            settings_obj = obj
        self._update_config(settings_obj, self)


class DefaultConfig(BaseConfig):
    __NEED_LOADED_SETTINGS__ = {}
    __DEFAULT_SETTINGS__ = None

    explicit = False

    def __init__(self, *args, **kwargs):
        super(DefaultConfig, self).__init__()
        self._make_default()

    def __getattr__(self, name):
        try:
            value = super(DefaultConfig, self).__getattr__(name)
        except NotLoadedError:
            if name in self.__NEED_LOADED_SETTINGS__:
                raise
            value = self._settings[name]
        if not self._validate_config_attr(name, value):
            raise ConfigError("Invalid setting: %r, %r" % (name, value))
        if isinstance(value, EmptyValue):
            return value.val
        return value

    def _validate_config_name(self, name, value):
        if not super(DefaultConfig, self)._validate_config_name(name, value):
            return False
        if self.explicit and name not in self.defaults:
            return False
        return True

    def _validate_config_value(self, name, value, type_=None):
        if isinstance(value, EmptyValue):
            return True
        if name in self.defaults:
            default_config_value = self.defaults[name]
            if isinstance(default_config_value, EmptyValue):
                if isinstance(value, type(default_config_value.val)) and \
                        EmptyValue.is_empty(value):
                    return True
                type_ = type(default_config_value.val)
            else:
                type_ = type(default_config_value)
        return super(DefaultConfig, self)._validate_config_value(name, value,
                                                                 type_)

    def _make_default(self):
        for name, value in self.defaults.iteritems():
            if self._validate_config_name(name, value):
                self._settings[name] = value

    @property
    def defaults(self):
        if self.__DEFAULT_SETTINGS__ is None:
            self.__DEFAULT_SETTINGS__ = {}
        return self.__DEFAULT_SETTINGS__


class CeleryConfig(DefaultConfig):
    """Celery config used by the project's async feature"""

    __NEED_LOADED_SETTINGS__ = {}
    __DEFAULT_SETTINGS__ = {
        "BROKER_URL": "",
        "CELERY_RESULT_BACKEND": default_empty(''),
        "CELERY_QUEUES": default_empty({}),
    }


class Config(DefaultConfig):

    """Defaults config. Specially you should load your own config from object,
    or even a config file such as `yaml`

    e.g.

        from walila.settings import settings

        class MyConfig(object):
            # some settings

        class CeleryConfig(object):
            # some stuff

        settings.from_object(MyConfig)

    """

    __NEED_LOADED_SETTINGS__ = {}
    __DEFAULT_SETTINGS__ = {
        # db
        "DB_POOL_SIZE": 10,
        "DB_MAX_OVERFLOW": 1,
        "DB_POOL_RECYCLE": 300,
        "DB_SETTINGS": default_empty({}),

        # default logger name
        "LOGGER_NAME": "SouthPay",
    }

    explicit = True

    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        self.celeryconfig = None

    def _after_update_config(self):
        super(Config, self)._after_update_config()
        from .config import load_app_config
        self.celeryconfig = CeleryConfig()
        self._update_celery_settings(load_app_config().celery_settings)

    def _update_celery_settings(self, settings):
        """Update celery settings"""
        if settings is None:
            logger.warning("No celery settings configured, using default.")
            return
        self.celeryconfig.from_object(settings)


settings = Config()
