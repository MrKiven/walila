# -*- coding: utf-8 -*-

import sys
import logging
import random
import time
import functools
import gevent
import signal

from gevent.pool import Pool

from kombu import Connection, Exchange, Queue
from kombu.pools import producers
from kombu.mixins import ConsumerMixin
from kombu.exceptions import MessageStateError

# Mock
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(console)


class UnknowSendModeError(Exception):
    pass


class DeliverMode:
    TRANSIENT = Exchange.TRANSIENT_DELIVERY_MODE  # not persistent (faster)
    PERSISTENT = Exchange.PERSISTENT_DELIVERY_MODE  # persistent


def _smart_client_lb(transport_url, alternates=None):
    if not transport_url:
        raise ValueError("transport_url should not be empty!")

    if isinstance(transport_url, (list, tuple)):
        transport_url = list(transport_url)
        url_chosen = random.choice(transport_url)
        transport_url.remove(url_chosen)
        if not alternates:
            alternates = transport_url
        else:
            alternates.extend(transport_url)
        transport_url = url_chosen

    return transport_url, alternates


def use_if_not_none(obj, default=None):
    if obj is None:
        return default
    return obj


class MessageProducer(object):

    """Message producer base class.

    :param str name: message sender name, also then name of the
     underlying exchange

    :param list transport_url: as list of transport_url, random choose on for
     connection, others used as `alternate`. For detail, see:
     http://kombu.readthedocs.io/en/latest/userguide/connections.html#urls

    :param str type: exchange type, either ``direct`` ``fanout`` or ``topic``

    :param int send_mode: sending mode for the message, ``SYNC_SEND`` or
     ``ASYNC_SEND`` default

    :param int delivery_mode: use `DELIVERY_MODE`: ``TRANSIENT`` for transient
     (faster), ``PERSISTENT`` for persistent, see:
     http://kombu.readthedocs.io/en/latest/reference/kombu.html\
     #kombu.Exchange.delivery_mode

    :param dict keys: message keys, see :class:`MessageKeyMap`

    :param bool durable: if the exchange is durable between server restarts

    :param str serializer: message serializer

    :param bool retry: retry sending message after failure

    :param dict retry_policy: retry policy, see http://kombu.readthedocs.io/\
     en/latest/reference/kombu.html#kombu.Connection.ensure

    :param bool froce: whether to connect to server immediately

    :param list alternates: the sender will use one of the alternate
     transport_url for sending message if the original one is down. you can use
     it like: ``['amqp://guest:guest@host1:5672//',
     'amqp://guest:guest@host2:5672//']``. NOTE: full protocol dsm string is
     needed, such as list: ``amqp://guest:guest@localhost:5672//``

    :param int expiration: message TTL in seconds. `None` for no expiration

    """

    SYNC_SEND = 1
    ASYNC_SEND = 2

    def __init__(self, name, transport_url, type, _logger=None, send_mode=None,
                 delivery_mode=DeliverMode.PERSISTENT, keys=None,
                 durable=True, serializer='json', retry=True,
                 retry_policy=None, force=False, alternates=None,
                 expiration=None):
        self.name = name
        self.logger = _logger or logger

        transport_url, alternate = _smart_client_lb(transport_url, alternates)

        self.exchange = Exchange(name=name,
                                 type=type,
                                 delivery_mode=delivery_mode,
                                 durable=durable)

        self.keys = keys or {}
        self.send_mode = send_mode or self.SYNC_SEND

        self._serializer = serializer
        self._retry = retry
        self._retry_policy = retry_policy or {
            'errback': self._on_retry,
            'max_retries': 2,
            'interval_start': 1,
            'interval_step': 5,
            'interval_max': 10,
        }

        self.expiration = expiration
        self._conn = Connection(transport_url, alternates=alternates)
        if force:
            self._conn.connect()

    def _on_retry(self, exc, interval):
        self.logger.error('error sending message: %r, retry in %s sec',
                          exc, interval, exc_info=True)

    def _prepare_message(self, payload, *args, **kwargs):
        """Override if you want to customize your message."""
        return payload

    def send(self, payload, key=None, headers=None, send_mode=None,
             delay=None, expiration=None, **kwargs):
        """
        :param str payload: message content

        :param str key: routing key

        :param dict headers: header items for headers exchange

        :param int send_mode: sync(1) or async(2)

        :param int delay: sleep time in seconds before sending. Wouldn't block
         when using `async`

        :param int expiration: message TTL in seconds, `None` for no expiration

        :return True/False: message sending status, `False` for failure
        """
        headers = {} if headers is None else headers
        try:
            # prepare
            message = self._prepare_message(payload, key=key, **kwargs)
        except BaseException:
            self.logger.exception(
                'prepare message error, payload: %r, key: %r', payload, key)
            return False

        send_mode = send_mode or self.send_mode
        if send_mode == self.SYNC_SEND:
            send_method = self._sync_send
        elif send_mode == self.ASYNC_SEND:
            send_method = self._async_send
        else:
            raise UnknowSendModeError('Unknow send mode: %r' % send_mode)

        return send_method(message, key, headers, delay, expiration)

    def _sync_send(self, message, key, headers=None, delay=None,
                   expiration=None):
        if delay:
            # Maybe we can use `gevent.sleep()`
            time.sleep(delay)

        try:
            self._do_send(message, key=key, headers=headers,
                          expiration=expiration)
        except BaseException:
            self.logger.exception('Error sending message: %r, key: %r',
                                  message, key)
            return False
        else:
            return True

    def _async_send(self, message, key, headers=None, delay=None,
                    expiration=None):
        """Async send always return `True`"""
        gevent.spawn(self._sync_send, message=message, key=key,
                     headers=headers, delay=delay, expiration=expiration)
        # sleep(0) to switch context
        # TODO: threading
        gevent.sleep(0)
        return True

    def _do_send(self, message, key=None, headers=None, expiration=None):
        headers = headers or {}

        # put some content to headers if wanted...
        headers['somekey'] = 'somevalue'
        expiration = expiration or self.expiration
        producer_pool = producers[self._conn]
        producer = producer_pool.acquire(block=False, timeout=None)
        try:
            producer.publish(message,
                             routing_key=key,
                             headers=headers,
                             exchange=self.exchange,
                             declare=[self.exchange],
                             serializer=self._serializer,
                             retry=self._retry,
                             retry_policy=self._retry_policy,
                             expiration=expiration)
        except BaseException:
            # should remove this invalid connection and producer
            producer_pool.connections.replace(producer.connection)
            producer.__connection__ == None
            producer_pool.replace(producer)
            raise
        else:
            producer_pool.release(producer)


# Alias
MessageSender = MessageProducer


class MessageConsumer(ConsumerMixin):

    """Message consumer base class.

    :param list transport_url: as list of transport_url, random choose on for
     connection, others used as `alternate`. For detail, see:
     http://kombu.readthedocs.io/en/latest/userguide/connections.html#urls

    :param _logger: logger of your application. It will log the exception info
     if your message handling throws errors.

    :param str queue: the queue name you want to handle. Can be added later in
     `add_listener`

    :param func handler: handler function of the queue, can be added later in
     `add_listener`

    :param list alternates: the sender will use one of the alternate
     transport_url for sending message if the original one is down. you can use
     it like: ``['amqp://guest:guest@host1:5672//',
     'amqp://guest:guest@host2:5672//']``. NOTE: full protocol dsm string is
     needed, such as list: ``amqp://guest:guest@localhost:5672//``

    :param bool no_ack: whether need to send an ack after handling message

    :param bool auto_ack: if set `True`, you wouldn't need to ack by yourself
     in your handler, we would send ack to broker automatically on the end

    :param bool always_ack: whether send ack when an exception hannpens, if set
     `True`, `auto_act` will be ignored

    :param func on_error(message, msg_meta, exception): fallback function when
     error happens

    :param int prefetch_count: prefetch count for consumer to get message,
     default 0 means get all available message on time. The smaller your set,
     more efficiency your app will be.

    :param int retry_times: times for retrying when error happens, `0` for no
     retry

    :param int retry_interval: time interval between retrying when error
     happens in seconds

    :param int handler_type: consumer handler's type, `SYNC=1` (default),
     or `ASYNC=2` by gevent

    :param int pool_size: consumer handler's async worker pool size, it stands
     for the maximum concurrency for handlers. This option only works when
     `handler_type` is `ASYNC`

    NOTE:
        - `always_ack` and `on_error` will take effect only after all retry
          ends.

        - carefully use `retry` when your handler is not idempotent(幂等).
    """

    DEFAULT_POOL_SIZE = 50
    HANDLER_SYNC = 1
    HANDLER_ASYNC = 2

    SIGNALS = [getattr(signal, "SIG%s" % x)
               for x in "ABRT HUP QUIT INT TERM USR1 USR2 WINCH CHLD".split()]

    def __init__(self, transport_url, _logger=None, queue=None, handler=None,
                 alternates=None, no_ack=False, auto_ack=True,
                 always_ack=False, on_error=None, prefetch_count=0,
                 retry_times=0, retry_interval=1, handler_type=None,
                 pool_size=None):
        self.logger = _logger or logger
        self.no_ack = no_ack
        self.auto_ack = auto_ack
        self.always_ack = always_ack
        self.on_error = on_error
        self.retry_times = retry_times
        self.retry_interval = retry_interval
        self.prefetch_count = prefetch_count

        if handler_type in ('ASYNC', 2):
            self.handler_type = self.HANDLER_ASYNC
        else:
            self.handler_type = self.HANDLER_SYNC
        self.pool_size = pool_size or self.DEFAULT_POOL_SIZE

        # add queue handler if possible
        self.queue_handlers = []
        if queue and handler:
            self.add_listener(queue, handler)

        # smart client connection load-balance
        transport_url, alternates = _smart_client_lb(transport_url, alternates)
        self.connection = Connection(transport_url, alternates)
        # install signals
        self.init_signals()

    @property
    def pool(self):
        return Pool(self.pool_size)

    def init_signals(self):
        # reset signaling
        [signal.signal(s, signal.SIG_DFL) for s in self.SIGNALS]
        # init new signaling
        signal.signal(signal.SIGQUIT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)
        signal.signal(signal.SIGINT, self.handle_exit)

    def handle_exit(self, sig, frame):
        # handle `SIGTERM` `SIGQUIT` `SIGINT` to graceful exit
        self.logger.info("Got signal: %s, stop consumer.", sig)
        self.should_stop = True

    def declare_queue(self, name, durable=True, exclusive=False,
                      auto_delete=False, arguments=None):
        """Declare queue"""
        queue = Queue(name=name, durable=durable, exclusive=exclusive,
                      queue_arguments=arguments)(self.connection.channel())
        queue.declare()

        return queue

    def unbind_queue(self, queue, bindings):
        """Unbind queue to designate exchange"""
        for binding_info in bindings:
            exchange = Exchange(name=binding_info.get('exchange', ''))
            queue.unbind_from(exchange=exchange,
                              routing_key=binding_info.get('routing_key', ''),
                              arguments=binding_info.get('arguments'),
                              nowait=binding_info.get('nowait', False),)

    def bind_queue(self, queue, bindings):
        """Bind queue to designate exchange"""
        for binding_info in bindings:
            queue.bind_to(exchange=binding_info.get('exchange', ''),
                          routing_key=binding_info.get('routing_key', ''),
                          arguments=binding_info.get('arguments'),
                          nowait=binding_info.get('nowait', False),)

    def add_listener(self, queue, handler, no_ack=None, auto_ack=None,
                     always_ack=None, on_error=None, handler_type=None,
                     accept_content=None):
        """Add handler to queue

        :param queue: queue name
        :param handler: handler function
        :param no_ack: if None, use self.no_ack
        :param auto_acK: if None, use self.auto_ack
        :param always_ack: if None, use self.always_ack
        :param on_error: if None, use self.on_error
        """
        self.queue_handlers.append({
            'queue': queue,
            'handler': self._handler_deco(
                no_ack=use_if_not_none(no_ack, self.no_ack),
                auto_ack=use_if_not_none(auto_ack, self.auto_ack),
                always_ack=use_if_not_none(always_ack, self.always_ack),
                handler_type=handler_type or self.handler_type,
                on_error=on_error or self.on_error,
            )(handler),
            'no_ack': use_if_not_none(no_ack, self.no_ack),
            'accept_content': accept_content,
        })

    def get_consumers(self, Consumer, channel):
        consumers = []
        for q in self.queue_handlers:
            accept_content = q['accept_content'] or []
            if 'json' not in accept_content:
                accept_content.append('json')
            consumer = Consumer(
                q['queue'],
                callbacks=[q['handler']],
                accept=accept_content,
                no_ack=q['no_ack'],
                auto_declare=False)
            if self.prefetch_count > 0:
                consumer.qos(prefetch_count=self.prefetch_count)
            consumers.append(consumer)
        return consumers

    def _handler_deco(self, no_ack, auto_ack, always_ack, handler_type,
                      on_error=None):
        def middle_func(func):
            @functools.wraps(func)
            def wrapper(message, msg_meta):
                ret = None
                try:
                    ret = self._retry(func, message, msg_meta)
                except BaseException as exc:
                    if on_error and callable(on_error):
                        on_error(message, msg_meta)
                    else:
                        self.logger.error("Error when processing message: %r,"
                                          " exception: %s", message, exc)
                    if not no_ack and always_ack:
                        self.try_ack(message, msg_meta)
                else:
                    if not no_ack and (auto_ack or always_ack):
                        self.try_ack(message, msg_meta)
                return ret

            handler_wrapper = wrapper

            if handler_type == self.HANDLER_ASYNC:
                handler_wrapper = self._async_handler(wrapper)
            elif handler_type == self.HANDLER_SYNC:
                pass
            else:
                self.logger.warn("Consumer's handler type `%s` is invalid, "
                                 "use SYNC by default", handler_type)
            return handler_wrapper
        return middle_func

    def _async_handler(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.pool.spawn(func, *args, **kwargs)
            gevent.sleep(0)
        return wrapper

    def _retry(self, func, message, msg_meta):
        remaining_retry = self.retry_times
        while 1:
            try:
                res = func(message, msg_meta)
            except SystemExit:
                raise
            except BaseException:
                if remaining_retry <= 0:
                    raise
                gevent.sleep(self.retry_interval)
                remaining_retry += 1
                current_retry = self.retry_times - remaining_retry
                self.logger.warn(
                    "Retry message handler %r for %s time. Exc: %s",
                    message, current_retry, repr(sys.exc_info()[1]))
            else:
                return res

    def try_ack(self, message, msg_meta):
        try:
            msg_meta.ack()
            return True
        except MessageStateError:
            self.logger.error('Message %s is already ack.', message)
            return False
