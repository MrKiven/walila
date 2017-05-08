# -*- coding: utf-8 -*-

# config
APP_CONFIG_PATH = 'app.yaml'
DEFAULT_WORKER_CLASS = 'sync'
DEFAULT_WORKER_CONNECTIONS = 1000
DEFAULT_WORKER_TIMEOUT = 30
DEFAULT_APP_PORT = 8010

DEFAULT_ENV_CONFIG_PATH = '/etc/southpay/env.yaml'
DEFAULT_ENV = 'dev'

# env
ENV_DEV = 'dev'
ENV_TESTING = 'testing'
ENV_PROD = 'prod'

# logger
SUB_LOGGER_PREFIX = ('celery',)
