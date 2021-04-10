"""
Utility function and classes
"""

import base64
import json
import os
import re

from datetime import timezone

import dockerpycreds
import dateutil.parser

from requests_toolbelt.utils import dump


def is_glob(string):
    """
    Returns True if string is a shell glob pattern
    """
    return bool(string and re.search(r"\*|\?|\[", string))


def print_response(got, *args, **kwargs):  # pylint: disable=unused-argument
    """
    Print response to aid in debugging
    """
    got.hook_called = True
    print(dump.dump_all(got).decode('utf-8'))
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


def get_docker_credentials(registry):
    """
    Gets the credentials from ~/.docker/config.json
    """
    config_file = os.path.join(
        os.getenv("DOCKER_CONFIG", os.path.expanduser(os.path.join("~", ".docker"))), "config.json")
    try:
        with open(config_file) as file:
            config = json.load(file)
    except OSError:
        return None
    registry = re.sub("^https?://", "", registry)
    for try_registry in (f"https://{registry}", f"http://{registry}", registry):
        try:
            auth = config['auths'][try_registry]['auth']
            return tuple(base64.b64decode(auth).decode('utf-8').split(':', 1))
        except KeyError:
            pass
    try:
        if registry in config['credHelpers']:
            store = dockerpycreds.Store(config['credHelpers'][registry])
            creds = store.get(registry)
            return creds['Username'], creds['Secret']
    except KeyError:
        pass
    return None
