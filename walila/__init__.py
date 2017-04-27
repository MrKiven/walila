# -*- coding: utf-8 -*-

"""
  Walila - Awesome toolkit for dobechina internal.
"""


from .config import load_app_config  # noqa
from .message import MessageProducer, MessageConsumer  # noqa

version_info = (0, 1, 0)
__version__ = ".".join([str(v) for v in version_info])
