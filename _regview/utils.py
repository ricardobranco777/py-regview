"""
Utility function and classes
"""

from collections import OrderedDict

from requests_toolbelt.utils import dump


class _Mixin:  # pylint: disable=too-few-public-methods
    @staticmethod
    def _print_response(got, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Print response to aid in debugging
        """
        got.hook_called = True
        data = dump.dump_all(got)
        print(data.decode('utf-8'))
        return got


# Adapted from https://docs.python.org/3/library/collections.html#collections.UserDict
class LRU(OrderedDict):
    'Limit size, evicting the least recently looked-up key when full'

    def __init__(self, *args, maxsize=64, **kwds):
        self.maxsize = maxsize
        super().__init__(*args, **kwds)

    def __getitem__(self, key):
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        if key in self:
            self.move_to_end(key)
        super().__setitem__(key, value)
        if len(self) > self.maxsize:
            oldest = next(iter(self))
            del self[oldest]
