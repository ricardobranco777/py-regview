"""
Auth related stuff
"""

import logging
import sys

import requests
from requests.exceptions import RequestException
from requests_toolbelt import GuessAuth

from .utils import _Mixin


class GuessAuth2(GuessAuth, _Mixin):
    """
    Support Token authentication as specified by https://docs.docker.com/registry/spec/auth/token/
    """
    url = None
    service = None

    def __init__(self, *args, debug=False, headers=None, verify=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = requests.Session()
        self.debug = debug
        if debug:
            self.session.hooks['response'].append(self._print_response)
        self.session.auth = (self.username, self.password)
        if headers:
            self.session.headers.update(headers)
        self.session.verify = verify
        self.session.mount("https://", requests.adapters.HTTPAdapter(pool_maxsize=100))

    def get_token(self, params=None, use_post=False):
        """
        Get token
        """
        params = params or {}
        if 'service' not in params:
            params.update({'service': self.service})
        try:
            method = "POST" if use_post else "GET"
            got = self.session.request(method, self.url, params=params)
            got.raise_for_status()
        except RequestException as err:
            logging.error("%s", err)
            sys.exit(1)
        data = got.json()
        return f"Bearer {data.get('token', data.get('access_token'))}"

    def _handle_token_auth_401(self, req, kwargs):
        params = requests.utils.parse_dict_header(req.headers['www-authenticate'])
        url = params['Bearer realm']
        del params['Bearer realm']

        if self.url is None:
            self.url = url
            self.service = params['service']

        if self.pos is not None:
            req.request.body.seek(self.pos)
        # Consume content and release the original connection
        # to allow our new request to reuse the same one.
        _ = req.content
        req.raw.release_conn()
        prep = req.request.copy()

        if self.debug:
            self._print_response(req)

        prep.headers['Authorization'] = self.get_token(params)
        _r = req.connection.send(prep, **kwargs)
        _r.request = prep
        return _r

    def handle_401(self, r, **kwargs):
        """
        Override this GuessAuth method to support token authentication
        """
        www_authenticate = r.headers.get('www-authenticate', '').lower()
        if 'basic' in www_authenticate:
            return self._handle_basic_auth_401(r, kwargs)
        if 'digest' in www_authenticate:
            return self._handle_digest_auth_401(r, kwargs)
        if 'bearer' in www_authenticate:
            return self._handle_token_auth_401(r, kwargs)
        return None
