# -*- coding: utf-8 -*-

import sys
import string
import random
import gevent

from walila.message import MessageProducer

transport_urls = ["amqp://guest:guest@localhost:5672//"]

producer = MessageProducer('my_test', transport_urls, 'fanout')


def random_message(length=6):
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for _ in range(length))

count = sys.argv[1]
for _ in xrange(int(count)):
    message = random_message()
    ret = producer.send(message, send_mode=MessageProducer.ASYNC_SEND)
    print 'Send message: %r, result: %s' % (message, ret)
    gevent.sleep(0.1)
