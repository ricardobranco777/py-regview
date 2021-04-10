"""
Docker Registry module
"""

import fnmatch
import logging
import sys

from functools import lru_cache
from urllib.parse import urlparse

import requests
from requests.exceptions import RequestException
from urllib3 import disable_warnings

from .auth import GuessAuth2
from .utils import get_docker_credentials, print_response


class DockerRegistry:
    """
    Class to implement Docker Registry methods
    """
    MANIFEST_V2 = "application/vnd.docker.distribution.manifest.v2+json"
    MANIFEST_V2_FAT = "application/vnd.docker.distribution.manifest.list.v2+json"

    def __init__(self, registry, auth=None, cert=None, headers=None, verify=True, debug=False):  # pylint: disable=too-many-arguments
        self.session = requests.Session()
        self.session.mount("http://", requests.adapters.HTTPAdapter(pool_maxsize=100))
        self.session.mount("https://", requests.adapters.HTTPAdapter(pool_maxsize=100))
        logging.basicConfig(format='%(levelname)s: %(message)s')
        if debug:
            self._enable_debug()
        auth = auth or get_docker_credentials(registry)
        if auth:
            auth = GuessAuth2(*auth, headers=headers, verify=verify, debug=debug)
        self.session.auth = auth
        self.session.cert = cert
        if headers:
            self.session.headers.update(headers)
        self.session.verify = verify
        disable_warnings()
        self.registry = self._check_registry(registry)

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
        self.session.hooks['response'].append(print_response)

    def _check_registry(self, registry):
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
            return registry
        try:
            got = self.session.get(f"https://{registry}/v2/")
            if got.status_code != 401:
                got.raise_for_status()
            return f"https://{registry}"
        except RequestException:
            try:
                got = self.session.get(f"http://{registry}/v2/")
                got.raise_for_status()
                return f"http://{registry}"
            except RequestException as err:
                logging.error("%s", err)
                sys.exit(1)
        if got.headers.get('docker-distribution-api-version') != 'registry/2.0':
            logging.error("Invalid registry: %s", registry)
            sys.exit(1)
        return None

    @lru_cache(maxsize=128)
    def _get_token_repo(self, repo, operations="pull"):
        """
        Get token for repo
        Note: operations should be a comma separated string of "pull", "push" or "delete"
        """
        if self.session.auth and self.session.auth.url:
            token = self.session.auth.get_token(params={"scope": f"repository:{repo}:{operations}"})
            return {"Authorization": token}
        return {}

    def _get_paginated(self, url, string, **kwargs):
        """
        Get paginated results
        """
        host = "://".join(urlparse(url)[0:2])
        while True:
            try:
                got = self.session.get(url, **kwargs)
                got.raise_for_status()
            except RequestException as err:
                logging.error("%s: %s", url, err)
                return None
            items = got.json()[string]
            if not items:
                return None
            yield from items
            if 'Link' in got.headers:
                url = requests.utils.parse_header_links(got.headers['Link'])[0]['url']
                if url.startswith("/v2/"):
                    url = f"{host}{url}"
            else:
                break

    def get_repos(self, pattern=None):
        """
        Get repositories
        """
        url = f"{self.registry}/v2/_catalog"
        headers = {}
        if self.session.auth and self.session.auth.url:
            token = self.session.auth.get_token(params={"scope": "registry:catalog:*"})
            headers.update({"Authorization": token})
        repos = self._get_paginated(url, "repositories", headers=headers)
        if repos and pattern:
            return fnmatch.filter(repos, pattern)
        return repos

    def get_tags(self, repo, pattern):
        """
        Get tags for specified repo
        """
        url = f"{self.registry}/v2/{repo}/tags/list"
        headers = self._get_token_repo(repo)
        tags = self._get_paginated(url, "tags", headers=headers)
        if tags and pattern:
            tags = fnmatch.filter(tags, pattern)
        return tags

    def get_manifest(self, repo, tag, fat=False):
        """
        Get the manifest
        """
        url = f"{self.registry}/v2/{repo}/manifests/{tag}"
        content_type = self.MANIFEST_V2
        if fat:
            content_type += f",{self.MANIFEST_V2_FAT}"
        headers = self._get_token_repo(repo)
        headers.update({"Accept": content_type})
        try:
            got = self.session.get(url, headers=headers)
            got.raise_for_status()
        except RequestException as err:
            fmt = "%s@%s: %s" if tag.startswith("sha256:") else "%s:%s: %s"
            logging.error(fmt, repo, tag, err)
            return None
        manifest = got.json()
        if manifest['schemaVersion'] != 2:
            return None
        manifest['docker-content-digest'] = got.headers.get('docker-content-digest')
        # Some registries don't return this header and need an additional HEAD request
        if not manifest['docker-content-digest']:
            try:
                got = self.session.head(url, headers=headers)
                got.raise_for_status()
                manifest['docker-content-digest'] = got.headers['docker-content-digest']
            except RequestException:
                pass
        return manifest

    def get_digest(self, repo, tag):
        """
        Get digest
        """
        url = f"{self.registry}/v2/{repo}/manifests/{tag}"
        content_type = self.MANIFEST_V2
        headers = self._get_token_repo(repo)
        headers.update({"Accept": content_type})
        try:
            got = self.session.head(url, headers=headers)
            got.raise_for_status()
            return got.headers.get('docker-content-digest')
        except RequestException as err:
            logging.error("%s:%s: %s", repo, tag, err)
        return None

    def delete(self, repo, digest):
        """
        Delete digest
        """
        url = f"{self.registry}/v2/{repo}/manifests/{digest}"
        content_type = self.MANIFEST_V2
        headers = self._get_token_repo(repo, "delete")
        headers.update({"Accept": content_type})
        try:
            got = self.session.delete(url, headers=headers)
            got.raise_for_status()
            return True
        except RequestException as err:
            logging.error("%s@%s: %s", repo, digest, err)
        return False

    def get_blob(self, repo, digest):
        """
        Get blob for repo
        """
        url = f"{self.registry}/v2/{repo}/blobs/{digest}"
        headers = self._get_token_repo(repo)
        try:
            got = self.session.get(url, headers=headers)
            got.raise_for_status()
        except RequestException as err:
            logging.error("%s@%s: %s", repo, digest, err)
            return None
        return got
