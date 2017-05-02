# -*- coding: utf-8 -*-

from walila.settings import settings


def test_default_settings():
    assert settings.DB_SETTINGS == {}
    assert settings.DB_POOL_SIZE == 10
    assert settings.DB_MAX_OVERFLOW == 1
    assert settings.DB_POOL_RECYCLE == 300


def test_set_settings():
    assert settings.DB_SETTINGS == {}
    settings.DB_SETTINGS = {'hello': 'world'}
    assert settings.DB_SETTINGS == {'hello': 'world'}
