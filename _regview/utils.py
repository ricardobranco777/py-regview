"""
Utility function and classes
"""

from datetime import timezone

import dateutil.parser

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


def pretty_size(size):
    """
    Converts a size in bytes to a string in KB, MB, GB or TB
    """
    units = (' ', 'K', 'M', 'G', 'T')
    for i in range(4, -1, -1):
        if size > 1024**i:
            return "%.2f%cB" % (float(size) / 1024**i, units[i])
    return None


def pretty_date(string):
    """
    Converts date/time string in ISO-8601 format to date(1)
    """
    # utc_date = datetime.fromisoformat(re.sub(r"\.\d+Z$", "+00:00", string))  # Python 3.7+ only
    utc_date = dateutil.parser.isoparse(string).replace(tzinfo=timezone.utc)
    return utc_date.astimezone().strftime("%a %b %d %H:%M:%S %Z %Y")
