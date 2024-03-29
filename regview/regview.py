#!/usr/bin/env python3
"""
regview
"""

import argparse
import platform
import re
import sys

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from getpass import getpass
from shutil import get_terminal_size

from .docker_registry import DockerRegistry
from .utils import pretty_date, pretty_size, is_glob
from . import __version__


# Architectures and operating systems that can be pushed to Docker Registry
GOARCH = ['386', 'amd64', 'arm', 'arm64', 'mips', 'mips64', 'mips64le',
          'mipsle', 'ppc64', 'ppc64le', 'riscv64', 's390x', 'wasm']
GOOS = ['aix', 'android', 'darwin', 'dragonfly', 'freebsd', 'illumos', 'ios',
        'js', 'linux', 'netbsd', 'openbsd', 'plan9', 'solaris', 'windows']


opts = None  # pylint: disable=invalid-name


def get_os_arch():
    """
    Get GOOS & GOARCH
    """
    arch = platform.machine().lower()
    # Fix arch
    if arch == "x86_64":
        arch = "amd64"
    elif arch in {"i386", "i686"}:
        arch = "386"
    elif arch in {"aarch64", "armv8l"}:
        arch = "arm64"
    elif arch == "armv7l":
        arch = "arm"
    return platform.system().lower(), arch


class DockerRegistryInfo(DockerRegistry):
    """
    Subclass of DockerRegistry
    """

    @lru_cache(maxsize=128)
    def get_info_digest(self, repo, digest, full=False):
        """
        Cached version of get_info() for digests
        """
        return self.get_info(repo, digest, full)

    @lru_cache(maxsize=128)
    def get_blob_cached(self, repo, digest):
        """
        Cached version of get_blob()
        """
        return self.get_blob(repo, digest)

    def get_info(self, repo, tag, full=False):
        """
        Get info from manifest v2
        """
        manifest = self.get_manifest(repo, tag, fat=True)
        if not manifest:
            manifest = self.get_manifest(repo, tag)
            if not manifest:
                return None
        if manifest and manifest.get('mediaType') == self.MANIFEST_V2_FAT:
            infos = []
            for item in manifest['manifests']:
                if opts.arch and item['platform']['architecture'] not in opts.arch or \
                        opts.os and item['platform']['os'] not in opts.os:
                    continue
                info = self.get_info_digest(repo, item['digest'], full)
                if not info:
                    continue
                # Fix digest for multi-arch
                info['Digest'] = manifest['docker-content-digest']
                if not opts.all:
                    return info
                keys = ('architecture', 'os', 'variant')
                info.update({k: item['platform'][k] for k in keys if k in item['platform']})
                keys = ('features', 'os.features')
                info.update({k: ",".join(info[k]) for k in keys if k in info})
                infos.append(info)
            return infos
        info = {
            'Digest': tag if tag.startswith("sha256:") else manifest['docker-content-digest'],
            'CompressedSize': sum(_['size'] for _ in manifest['layers']),
            'ID': manifest['config']['digest']}
        if full:
            info.update(self.get_blob_cached(repo, info['ID']).json())
            if not opts.raw:
                info['created'] = pretty_date(info['created'])
                info['CompressedSize'] = pretty_size(info['CompressedSize'])
        return info

    def print_fullinfo(self, repo, tag="latest"):
        """
        Print full info about image
        """
        # Filter by current arch & OS if neither --all, --arch or --os were specified
        if not opts.all:
            os_, arch = get_os_arch()
            opts.os, opts.arch = {os_}, {arch}
        infos = self.get_info(repo, tag, full=True)
        if not opts.all:
            opts.os = opts.arch = None
        if infos is None:
            return
        if isinstance(infos, list):
            for info in infos:
                for key, value in sorted(info.items()):
                    if key in {"config", "history", "rootfs"}:
                        continue
                    print(f"{key:<20}\t{value}")
                print()
            return
        info = infos
        keys = (
            'architecture', 'author', 'created', 'docker_version', 'os',
            'CompressedSize', 'ID', 'Digest')
        data = {key: info[key] for key in keys if info.get(key)}
        keys = (
            'Cmd', 'Entrypoint', 'Env', 'ExposedPorts',
            'Healthcheck', 'Labels', 'OnBuild', 'Shell',
            'StopSignal', 'User', 'Volumes', 'WorkingDir')
        if opts.verbose:
            data.update({key: info['config'][key] for key in keys if info['config'].get(key)})
        for key in sorted(data, key=str.casefold):
            print(f"{key:<20}\t{data[key]}")
        if opts.verbose:
            self.print_history(info['history'])

    @staticmethod
    def print_history(history):
        """
        Print image history
        """
        for i, item in enumerate(history):
            print(f"History[{i}]\t\t{item['created_by']}")

    @staticmethod
    def print_info(repo, tag, info, fmt):
        """
        Print info about image
        """
        docker_id = info['ID']
        if not opts.no_trunc:
            docker_id = docker_id[len("sha256:"):len("sha256:") + 12]
        values = [f"{repo}:{tag}"]
        if opts.digests:
            values.append(info['Digest'])
        values.append(docker_id)
        if opts.verbose:
            created = info['created']
            values.append(created)
        if opts.all:
            values.append(info['os'])
            values.append(info['architecture'])
        print(fmt.format(*values))

    def get_images(self, repos, pattern_tag=None):
        """
        Get images"
        """
        with ThreadPoolExecutor(max_workers=2) as executor:
            yield from executor.map(lambda r: (r, self.get_tags(r, pattern_tag)), repos)

    def delete_images(self, repo_pattern, tag_pattern):
        """
        Delete images
        """
        # Do not try to get the catalog when globbing only the tag
        repos = self.get_repos(repo_pattern) if is_glob(repo_pattern) or repo_pattern is None \
            else [repo_pattern]
        if not repos:
            return
        for repo in repos:
            tags = self.get_tags(repo, tag_pattern)
            with ThreadPoolExecutor() as executor:
                digests = executor.map(lambda t, r=repo: self.get_digest(r, t), tags)
                for digest in digests:
                    if opts.dry_run or opts.verbose:
                        print(f"{repo}@{digest}")
                    if not opts.dry_run:
                        self.delete(repo, digest)

    def print_all(self, repo_pattern, tag_pattern):
        """
        Print all
        """
        # Do not try to get the catalog when globbing only the tag
        repos = self.get_repos(repo_pattern) if is_glob(repo_pattern) or repo_pattern is None \
            else [repo_pattern]
        if not repos:
            return
        image_width = int(get_terminal_size().columns / 2)
        fmt = OrderedDict({
            "REPOSITORY:TAG": f"{{:<{image_width}}}",
            "DIGEST": "{:<72}" if opts.digests else None,
            "IMAGE ID": "{:<72}" if opts.no_trunc else "{:<12}",
            "CREATED": "{:<31}" if opts.verbose else None,
            "OS": "{:<8}" if opts.all else None,
            "ARCH": "{}" if opts.all else None})
        fmt = {k: fmt[k] for k in fmt if fmt[k]}
        keys = fmt.keys()
        fmt = "  ".join(fmt.values())
        print(fmt.format(*keys))
        full = opts.all or opts.verbose
        with ThreadPoolExecutor() as executor:
            for repo, tags in self.get_images(repos, tag_pattern):
                if tags is None:
                    continue
                for tag, infos in executor.map(
                        lambda t, r=repo: (t, self.get_info(r, t, full=full)), tags):
                    if not isinstance(infos, list):
                        infos = [infos]
                    for info in infos:
                        if info is None:
                            continue
                        if opts.arch and info['architecture'] not in opts.arch or \
                                opts.os and info['os'] not in opts.os:
                            continue
                        self.print_info(repo, tag, info, fmt)


def parse_opts():
    """
    Parse options and arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-a', '--all', action='store_true',
        help="Print information for all architectures")
    parser.add_argument(
        '--arch', action='append', choices=GOARCH,
        help="Target architecture.  May be specified multiple times")
    parser.add_argument(
        '--os', action='append', choices=GOOS,
        help="Target OS.  May be specified multiple times")
    parser.add_argument(
        '-c', '--cert',
        help="Client certificate filename (may contain unencrypted key)")
    parser.add_argument(
        '-k', '--key',
        help="Client private key filename (unencrypted)")
    parser.add_argument(
        '-C', '--cacert',
        help="CA certificate for server")
    parser.add_argument(
        '--debug', action='store_true',
        help="Enable debug")
    parser.add_argument(
        '--digests', action='store_true',
        help="Show digests")
    parser.add_argument(
        '--insecure', action='store_true',
        help="Allow insecure server connections")
    parser.add_argument(
        '--no-trunc', action='store_true',
        help="Don't truncate output")
    parser.add_argument(
        '--raw', action='store_true',
        help="Raw values for date and size")
    parser.add_argument(
        '-u', '--username',
        help="Username for authentication")
    parser.add_argument(
        '-p', '--password',
        help="Password for authentication")
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help="Show more information")
    parser.add_argument(
        '--delete', action='store_true',
        help="Delete images. USE WITH CAUTION!")
    parser.add_argument(
        '--dry-run', action='store_true',
        help="Used with --delete: only show the images that would be deleted")
    parser.add_argument(
        '-V', '--version', action='store_true',
        help="Show version and exit")
    parser.add_argument('image', nargs='?', help="REGISTRY[/REPOSITORY[:TAG|@DIGEST]]")
    return parser.parse_args()


def main():
    """
    Main function
    """
    global opts  # pylint: disable=global-statement,invalid-name
    opts = parse_opts()

    if opts.version:
        print(__version__)
        sys.exit(0)
    if not opts.image:
        print(f"Usage: {sys.argv[0]} [OPTIONS] REGISTRY[/REPOSITORY[:TAG|@DIGEST]]")
        sys.exit(1)
    if opts.username and not opts.password:
        opts.password = getpass("Password: ")
    if opts.arch or opts.os:
        opts.arch, opts.os = set(opts.arch if opts.arch else []), set(opts.os if opts.os else [])
        opts.all = True
    match = re.match(r'((?:https?://)?[^:/]+(?::[0-9]+)?)/*(.*)', opts.image)
    registry, image = match.group(1), match.group(2)
    pattern_repo = pattern_tag = None
    if '@' not in image and is_glob(image):
        pattern_repo, pattern_tag = image.split(':', 1) if ':' in image else (image, None)
    with DockerRegistryInfo(
            registry,
            auth=(opts.username, opts.password) if opts.username else None,
            cert=(opts.cert, opts.key) if opts.cert and opts.key else opts.cert,
            headers={'User-Agent': f"regview/{__version__}"},
            verify=opts.cacert if opts.cacert else not opts.insecure,
            debug=opts.debug) as reg:
        if image and not pattern_repo:
            sep = '@' if '@' in image else ':'
            if opts.delete:
                reg.delete_images(*image.split(sep, 1))
            else:
                reg.print_fullinfo(*image.split(sep, 1))
        else:
            if opts.delete:
                sys.exit(f"To delete all images use {registry}:*:*")
            reg.print_all(pattern_repo, pattern_tag)
