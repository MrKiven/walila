# -*- coding: utf-8 -*-

import sys
import logging
import logging.config

from walila.utils import obj2str


def setup_logger_cls():

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
            from .settings import settings
            super(DefaultLogger, self).__init__(*args, **kwargs)
            self.name = "{name}.{raw}".format(
                name=settings.LOGGER_NAME, raw=self.name)

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
            'syslog_udp': {
                'level': 'INFO',
                'class': 'logging.handlers.SysLogHandler',
                'address': '/run/systemd/journal/syslog',
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


def gen_logging_dictconfig(logger_name):
    return _gen_console_logging_config(logger_name)


def setup_loggers(logger_name):
    setup_logger_cls()
    conf = gen_logging_dictconfig(logger_name)
    logging.config.dictConfig(conf)


class WalilaFormatter(logging.Formatter):

    def _format(self, msg):
        """Custom format log message."""
        body = obj2str(msg)
        return body

    def format(self, record):
        record.msg = self._format(record.msg)
        return super(WalilaFormatter, self).format(record)