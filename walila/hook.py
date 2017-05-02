# -*- coding: utf-8 -*-

import collections


class StopHook(Exception):
    """Stop calling next hooks"""

    def __init__(self, value, meta=None):
        self.value = value
        self.meta = meta

    def __str__(self):
        return "<StopHook value={!r} meta={!r}>".format(self.value, self.meta)

    __repr__ = __str__


class Hook(object):

    def __init__(self, event, func):
        self.event = event
        self.func = func

    def __call__(self, *args, **kwargs):
        # XXX: do not need return
        return self.func(*args, **kwargs)

    def __str__(self):
        return "<Hook event={!r} func={!r}>".format(
            self.event, self.func.__name__)

    __repr__ = __str__


class HookRegistry(object):

    def __init__(self):
        self._registry = collections.defaultdict(list)

    def __getattr__(self, attr):
        """Call all hooks which must be start with `on_`.

           registry.on_api_called()

        """
        if not attr.startswith('on_'):
            raise AttributeError("{} object has no attribute {}".format(
                self.__class__.__name__, attr))
        hooks = self._registry[attr[3:]]
        return lambda *args, **kwargs: [hook(*args, **kwargs)
                                        for hook in hooks]

    def register(self, hook):
        """Register a function which decorator by `define_hook`.
        """
        self._registry[hook.event].append(hook.func)

    def clear(self):
        """Clear all hooks"""
        self._registry.clear()


def define_hook(event):
    """Utilty for hook definition,

        @define_hook(event='before_api_called')
        def some_hook():
            # do stuff
    """
    def deco(func):
        return Hook(event, func)
    return deco

hook_registry = HookRegistry()
