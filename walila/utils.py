# -*- coding: utf-8 -*-

import sys
import os


class EmptyValue(object):

    def __init__(self, val):
        if not self.is_empty(val):
            raise ValueError('Error invalid empty value: %s' % val)
        self.val = val

    @staticmethod
    def is_empty(val):
        """
        empty value means the following stuff:

            ``None``, ``[]``, ``()``, ``{}``, ``''``
        """
        return val not in (False, 0) and not val


class _Missing(object):

    def __repr__(self):
        return 'no value'

    def __reduce__(self):
        return '_missing'

_missing = _Missing()


class cached_property(property):
    """
    https://github.com/pallets/werkzeug/blob/master/werkzeug/utils.py#L35
    """
    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __get__(self, obj, otype=None):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, _missing)
        if value is _missing:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value


def obj2str(obj):
    if isinstance(obj, unicode):
        return obj.encode('utf8')
    if isinstance(obj, (str, int, float, bool)):
        return str(obj)
    return repr(obj)


def get_cpu_count():
    if 'bsd' in sys.platform or sys.platform == 'darwin':
        cpu_count = 4
    else:
        cpu_count = os.sysconf('SC_NPROCESSORS_ONLN')
    return cpu_count
