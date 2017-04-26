# -*- coding: utf-8 -*-

import os
import pytest

from lib.config import load_app_config

current_path = os.path.dirname(os.path.abspath(__file__))
test_config_path = os.path.join(current_path, 'test.ini')


@pytest.fixture
def app_config():
    return load_app_config(path=test_config_path)


def test_load_app_config(app_config):
    assert app_config.env == 'dev'
    assert app_config.hello == 'world'
    assert app_config.fuck == 'shit'
    assert app_config.debug is True

    assert app_config.configs == {'hello': 'world', 'fuck': 'shit'}


def test_singleton(app_config):
    assert app_config is load_app_config(path=test_config_path)
