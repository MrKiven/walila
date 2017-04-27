# -*- coding: utf-8 -*-


from lib.config import load_app_config  # noqa
from lib.message import MessageProducer, MessageConsumer  # noqa

version_info = (0, 1, 0)
__version__ = ".".join([str(v) for v in version_info])
