# -*- coding: utf-8 -*-

import logging

from walila.message import MessageConsumer
from walila.log import setup_loggers

setup_loggers('SouthPay')
logger = logging.getLogger(__name__)

transport_urls = ["amqp://guest:guest@localhost:5672//"]


def handler(message, msg_meta):
    logger.info('Got message: %s', message)
    logger.info('Got msg meta: %s', msg_meta)

consumer = MessageConsumer(transport_urls)
queue = consumer.declare_queue('MyQueue')
consumer.add_listener(
    queue, handler, handler_type=MessageConsumer.HANDLER_ASYNC)
consumer.run()
