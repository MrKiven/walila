# -*- coding: utf-8 -*-

from walila.consts import ENV_DEV, ENV_TESTING, ENV_PROD


def _validate_env(ctx, argument, value):
    if value not in (ENV_DEV, ENV_TESTING, ENV_PROD):
        raise RuntimeError("Invalid env: %s" % value)
    return value
