# -*- coding: utf-8 -*-

import sys
import logging
from importlib import import_module

from .log import setup_loggers
from .config import load_app_config, load_env_config
from .utils import EmptyValue
from .consts import ENV_DEV, ENV_TESTING, ENV_PROD


logger = logging.getLogger(__name__)


def env():
    return load_env_config().env


def is_in_dev():
    return load_env_config().env == ENV_DEV


def is_in_testing():
    return load_env_config().env == ENV_TESTING


def is_in_prod():
    return load_env_config().env == ENV_PROD


initialized = False
settings_updated = False
loggers_initialized = False
sessions_created = False


def initialize():
    """Initialize worker process envrionment, include:
    logging, settings, db sessions etc. It should be called before all other
    operations are taken, right after a worker is forked (``post_fork``) or
    in cmd entry points. Please note the other of these operations.
    """
    global initialized
    if initialized:
        return logger.warning("Env is already initialized, skipping")
    init_loggers()
    update_settings()
    create_db_sessions()
    initialized = True


def init_loggers():
    global loggers_initialized
    if loggers_initialized:
        return logger.warning("logging is already initialized, skipping")
    setup_loggers(
        load_app_config().logger_name, env(), load_app_config().app_log_path)
    loggers_initialized = True


def update_settings():
    global settings_updated
    if settings_updated:
        return logger.warning("settings is already updated, skipping")

    app_config = load_app_config()
    from .settings import settings
    sys.path.insert(0, '.')
    mo_settings = import_module(app_config.app_settings_uri)
    settings.from_object(mo_settings)
    settings_updated = True


def create_db_sessions():
    """Create all db sessions, (rely ``update_settings``)"""
    global sessions_created
    if sessions_created:
        return logger.warning("db sessions are already created, skipping")
    from .db import db_manager, patch_column_type_checker
    from .settings import settings
    patch_column_type_checker()
    if not EmptyValue.is_empty(settings.DB_SETTINGS):
        db_manager.create_sessions()
    sessions_created = True
