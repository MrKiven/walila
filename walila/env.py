# -*- coding: utf-8 -*-

import logging
from importlib import import_module

from .log import setup_loggers
from .config import load_app_config


logger = logging.getLogger(__name__)

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
    setup_loggers(load_app_config().logger_name)
    loggers_initialized = True


def update_settings():
    global settings_updated
    if settings_updated:
        return logger.warning("settings is already updated, skipping")

    app_config = load_app_config()

    from .settings import settings
    mo_settings = import_module(app_config.app_settings_uri)
    settings.from_object(mo_settings)
    settings_updated = True


def create_db_sessions():
    """Create all db sessions, (rely ``update_settings``)"""
    global sessions_created
    if sessions_created:
        return logger.warning("db sessions are already created, skipping")
    from .db import db_manager, patch_column_type_checker
    patch_column_type_checker()
    db_manager.create_sessions()
    sessions_created = True
