"""
Utility function and classes
"""

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
