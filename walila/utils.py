# -*- coding: utf-8 -*-


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
