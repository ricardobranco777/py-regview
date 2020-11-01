"""
Docker Registry module
"""

import base64
import fnmatch
import json
import logging
import os
import re
import sys

from urllib.parse import urlparse

import requests
from requests.exceptions import RequestException
from urllib3 import disable_warnings

from _regview.auth import GuessAuth2
from _regview.utils import _Mixin, LRU


class DockerRegistry(_Mixin):
    """
    Class to implement Docker Registry methods
    """
    _token_cache = LRU()

    def __init__(self, registry, auth=None, cert=None, headers=None, verify=True, debug=False):  # pylint: disable=too-many-arguments
        self.session = requests.Session()
        self.session.mount("http://", requests.adapters.HTTPAdapter(pool_maxsize=100))
        self.session.mount("https://", requests.adapters.HTTPAdapter(pool_maxsize=100))
        logging.basicConfig(format='%(levelname)s: %(message)s')
        if debug:
            self._enable_debug()
        auth = auth or self._get_creds(registry)
        if auth:
            auth = GuessAuth2(*auth, headers=headers, verify=verify, debug=debug)
        self.session.auth = auth
        self.session.cert = cert
        if headers:
            self.session.headers.update(headers)
        self.session.verify = verify
        disable_warnings()
        self._fix_registry(registry)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if isinstance(self.session.auth, GuessAuth2):
            self.session.auth.session.close()
        self.session.close()

    def _enable_debug(self):
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
        self.session.hooks['response'].append(self._print_response)

    def _fix_registry(self, registry):
        """
        Check if registry starts with a scheme and adjust accordingly
        """
        if registry.startswith(("http://", "https://")):
            try:
                got = self.session.get(f"{registry}/v2/")
                got.raise_for_status()
            except RequestException as err:
                logging.error("%s", err)
                sys.exit(1)
            self.registry = registry
        else:
            try:
                got = self.session.get(f"https://{registry}/v2/")
                got.raise_for_status()
                self.registry = f"https://{registry}"
            except RequestException:
                try:
                    got = self.session.get(f"http://{registry}/v2/")
                    got.raise_for_status()
                    self.registry = f"http://{registry}"
                except RequestException as err:
                    logging.error("%s", err)
                    sys.exit(1)
        if got.headers.get('docker-distribution-api-version') != 'registry/2.0':
            logging.error("Invalid registry: %s", registry)
            sys.exit(1)

    @staticmethod
    def _get_creds(registry):
        """
        Gets the credentials from ~/.docker/config.json
        """
        config_file = os.path.join(
            os.getenv("DOCKER_CONFIG", os.path.expanduser(os.path.join("~", ".docker"))),
            "config.json")
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
        return None

    def _get(self, url, headers=None, **kwargs):
        """
        Cache tokens for repository URL's to avoid so many 401's
        and calling the auth server that many times
        """
        path = urlparse(url).path
        repo = None
        headers = headers or {}
        if not path.startswith("/v2/_"):
            repo = "/".join(path.split("/")[2:-2])
            if repo in self._token_cache:
                headers.update({"Authorization": self._token_cache[repo]})
        got = self.session.get(url, headers=headers, **kwargs)
        got.raise_for_status()
        if repo and repo not in self._token_cache:
            token = got.request.headers.get('Authorization')
            if token and token.startswith("Bearer "):
                self._token_cache[repo] = token
        return got

    def _get_paginated(self, url, string):
        """
        Get paginated results
        """
        items = []
        while True:
            try:
                got = self._get(url)
            except RequestException as err:
                logging.error("%s: %s", url, err)
                return None
            items.extend(got.json()[string])
            if 'Link' in got.headers:
                url = requests.utils.parse_header_links(got.headers['Link'])[0]['url']
                if url.startswith("/v2/"):
                    url = f"{self.registry}{url}"
            else:
                break
        return items

    def get_repos(self, pattern=None):
        """
        Get repositories
        """
        repos = self._get_paginated(f"{self.registry}/v2/_catalog", "repositories")
        if repos and pattern:
            return fnmatch.filter(repos, pattern)
        return repos

    def get_tags(self, repo, pattern):
        """
        Get tags for specified repo
        """
        tags = self._get_paginated(f"{self.registry}/v2/{repo}/tags/list", "tags")
        if tags and pattern:
            tags = fnmatch.filter(tags, pattern)
        return tags

    def get_manifest(self, repo, tag, fat=False):
        """
        Get the manifest
        """
        url = f"{self.registry}/v2/{repo}/manifests/{tag}"
        content_type = "application/vnd.docker.distribution.manifest.v2+json"
        if fat:
            content_type = "application/vnd.docker.distribution.manifest.list.v2+json"
        try:
            got = self._get(url, headers={"Accept": content_type})
        except RequestException as err:
            fmt = "%s@%s: %s" if tag.startswith("sha256:") else "%s:%s: %s"
            logging.error(fmt, repo, tag, err)
            return None
        manifest = got.json()
        if not fat:
            manifest['docker-content-digest'] = got.headers['docker-content-digest']
        return manifest

    def get_blob(self, repo, digest):
        """
        Get blob for repo
        """
        try:
            got = self._get(f"{self.registry}/v2/{repo}/blobs/{digest}")
        except RequestException as err:
            logging.error("%s@%s: %s", repo, digest, err)
            return None
        return got
