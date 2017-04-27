# -*- coding: utf-8 -*-

from ..message import MessageConsumer

transport_urls = ["amqp://guest:guest@localhost:5672//"]

def handler(message, msg_meta):
    print 'Got message: ', message
    print 'Got msg meta: ', msg_meta

consumer = MessageConsumer(transport_urls)
queue = consumer.declare_queue('MyQueue')
consumer.add_listener(queue, handler, handler_type=MessageConsumer.HANDLER_ASYNC)
consumer.run()
