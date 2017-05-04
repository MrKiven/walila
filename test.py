# -*- coding: utf-8 -*-


"""
  A simple test producer
"""

import sys
import time
import signal
import gevent

from walila.example.task import task_manager

count = 0
start = time.time()


def handle_int(sig, frame):
    print "Got signal: {}, quit!".format(sig)
    usage = time.time() - start
    print "Total: %d, Usage: %s s, qps: %s per second" % (count, usage, count/usage)
    sys.exit(0)


def send_task():
    global count
    while 1:
        print gevent.getcurrent(), ', task id: ', task_manager.perform('add', 1, 1), 'send success!'
        count += 1
        gevent.sleep(0)


signal.signal(signal.SIGINT, handle_int)
signal.signal(signal.SIGQUIT, handle_int)
signal.signal(signal.SIGTERM, handle_int)

greenlets = []

for _ in xrange(int(sys.argv[1])):
    g = gevent.spawn(send_task)
    greenlets.append(g)

for g in greenlets:
    g.join()
