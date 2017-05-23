# -*- coding: utf-8 -*-

import sys
import logging
import logging.config

from walila.utils import obj2str
from walila.consts import SUB_LOGGER_PREFIX, ENV_DEV, SHIELDS_LOGGERS


def setup_logger_cls():

    from walila.config import load_app_config

    class DefaultLogger(logging.getLoggerClass()):

        def error(self, *args, **kwargs):
            try:
                return super(DefaultLogger, self).error(*args, **kwargs)
            finally:
                # do somestuff
                pass

        def warning(self, *args, **kwargs):
            try:
                return super(DefaultLogger, self).warning(*args, **kwargs)
            finally:
                pass

        warn = warning

        def __init__(self, *args, **kwargs):
            app_config = load_app_config()
            super(DefaultLogger, self).__init__(*args, **kwargs)
            if self.name.startswith(SHIELDS_LOGGERS):
                # set `dicttoxml` logger level to `ERROR`
                self.level = logging.ERROR
            if self.name.startswith(SUB_LOGGER_PREFIX):
                self.name = "{}.{}".format(app_config.logger_name, self.name)

    logging.setLoggerClass(DefaultLogger)


def _gen_console_logging_config(logger_name):
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'loggers': {
            logger_name: {
                'handlers': ['console'],
                'propagate': False,
                'level': 'INFO',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'console',
                'stream': sys.stdout,
            },
            'console_error': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'console',
            },
        },
        'formatters': {
            'console': {
                '()': 'walila.log.WalilaFormatter',
                'format': ('%(asctime)s %(levelname)-6s '
                           '%(name)s[%(process)d] %(message)s')
            },
        },
    }


def _gen_syslog_logging_config(logger_name):
    """Using rsyslog in linux..."""
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'root': {
            'handlers': ['syslog'],
            'level': 'INFO',
        },
        'loggers': {
            logger_name: {
                'handlers': ['syslog'],
                'propagate': False,
                'level': 'INFO',
            },
            'gunicorn.*': {
                'handlers': ['syslog'],
                'propagate': False,
                'level': 'INFO',
            },
        },
        'handlers': {
            'syslog': {
                'level': 'INFO',
                'class': 'logging.handlers.SysLogHandler',
                'address': ('localhost', 514),
                'facility': 'local6',
                'formatter': 'syslog',
            },
        },
        'formatters': {
            'syslog': {
                '()': 'walila.log.WalilaFormatter',
                'format': '%(name)s[%(process)d]: %(message)s',
            },
        },
    }


def _gen_file_logging_config(logger_name, log_path):
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'root': {
            'handlers': ['filelog'],
            'level': 'INFO',
        },
        "loggers": {
            logger_name: {
                "handlers": ['filelog'],
                "propagate": False,
                "level": "INFO",
            },
        },
        "handlers": {
            "filelog": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": log_path,
                "encoding": "utf8",
                "formatter": "filelog"
            },
        },
        "formatters": {
            "filelog": {
                'format': ('%(asctime)s %(levelname)-6s '
                           '%(name)s[%(process)d] %(message)s')
            },
        },
    }


def gen_logging_dictconfig(logger_name, env, log_path):
    if env == ENV_DEV:
        conf = _gen_console_logging_config(logger_name)
    else:
        conf = _gen_file_logging_config(logger_name, log_path=log_path)
    return conf


def setup_loggers(logger_name, env, log_path=None):
    setup_logger_cls()
    conf = gen_logging_dictconfig(logger_name, env, log_path)
    logging.config.dictConfig(conf)


class WalilaFormatter(logging.Formatter):

    def _format(self, msg):
        """Custom format log message."""
        body = obj2str(msg)
        return body

    def format(self, record):
        record.msg = self._format(record.msg)
        return super(WalilaFormatter, self).format(record)
