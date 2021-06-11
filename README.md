# regview

View the contents of a Docker Registry v2

[![Build Status](https://travis-ci.com/ricardobranco777/regview.svg?branch=master)](https://travis-ci.org/ricardobranco777/regview)

## Usage

```
regview [OPTIONS] REGISTRY[/REPOSITORY[:TAG|@DIGEST]]
  -h, --help            show this help message and exit
  -a, --all             Print information for all architectures
  --arch {386,amd64,arm,arm64,mips,mips64,mips64le,mipsle,ppc64,ppc64le,riscv64,s390x,wasm}
                        Target architecture. May be specified multiple times
  --os {aix,android,darwin,dragonfly,freebsd,illumos,ios,js,linux,netbsd,openbsd,plan9,solaris,windows}
                        Target OS. May be specified multiple times
  -c CERT, --cert CERT  Client certificate filename (may contain unencrypted key)
  -k KEY, --key KEY     Client private key filename (unencrypted)
  -C CACERT, --cacert CACERT
                        CA certificate for server
  --debug               Enable debug
  --insecure            Allow insecure server connections
  --no-trunc            Don't truncate output
  --raw                 Raw values for date and size
  -u USERNAME, --username USERNAME
                        Username for authentication
  -p PASSWORD, --password PASSWORD
                        Password for authentication
  -v, --verbose         Show more information
  -V, --version         Show version and exit
  --delete              Delete images. USE WITH CAUTION!
  --dry-run             Used with --delete: only show the images that would be deleted
```

## Notes

- If only the registry is specified, `regview` will list all images and the `-v` (`--verbose`) option needs to fetch an additional manifest.
- In listing mode, shell style pattern matching is supported in repositories and tags like `busybo?/late*` or `debian:[7-9]`.
- If an image is specified, the `-v` (`--verbose`) option also displays the image's history.
- If the `--all` option is specified and the registry holds multiple images for each supported platform/architecture, you can fetch the information for each one using the image's digest.

## Requirements

- Python 3.6+
- requests
- requests-toolbet
- python-dateutil

## Supported authentication methods

- HTTP Basic Authentication
- HTTP Digest Authentication
- Token Authentication

## Supported registries

- Docker Distribution
- Amazon ECR (get credentials with `aws ecr get-login` and run `docker login`)
- Azure ACR (get credentials with `az acr credential show -n` and run `docker login`)
- Google GCR (run `gcloud auth configure-docker` and use `[ZONE.]gcr.io/<PROJECT>/*` to list the registry)
- ~~Docker Hub~~ Dropped due to stupid [rate limit](https://docs.docker.com/docker-hub/download-rate-limit/). You can use `registry.hub.docker.com/<IMAGE>` though.

## Deleting images

To delete tagged images you can use the `--delete` option.  Use the `--dry-run` option is you want to view the images that would be deleted.

Steps:
1. Make sure that the registry container has the `REGISTRY_STORAGE_DELETE_ENABLED` environment variable (or relevant entry in `/etc/docker/registry/config.yml`) set to `true`.
1. Run `regview --delete ...`
1. Either stop or restart the registry cointainer in maintenance (read-only) mode by setting the `REGISTRY_STORAGE_MAINTENANCE_READONLY` environment variable to `true` (or editing the relevant entry in `/etc/docker/registry/config.yml`).
1. Run `docker run --rm --volumes-from $CONTAINER registry:2 garbage-collect /etc/docker/registry/config.yml` if the container was stopped. Otherwise `docker exec $CONTAINER garbage-collect /etc/docker/registry/config.yml` if the container is in maintenance mode.
1. Optionally run the same command from above appending `--delete-untagged` to delete untagged images.
1. Restart the registry container in production mode.

NOTES:
- The above commands assume that the volume containing the registry filesystem is mounted at `/var/lib/registry` in the registry container.
- The `-m` (`--delete-untagged`) option was added to Docker Registry 2.7.0
- The `-m` (`--delete-untagged`) option is [BUGGY](https://github.com/distribution/distribution/issues/3178) with multi-arch images. The only workaround is to push those images independently adding the archictecture name to the tag.
- USE AT YOUR OWN RISK!

## Podman

To use with [Podman](https://podman.io/):

`alias podman=docker`

## Bugs / Limitations

- The client key must be unencrypted until this [issue in Python Requests](https://github.com/psf/requests/issues/1573) is fixed.
- Python Requests doesn't yet support HTTP/2.  I tried with [httpx](https://github.com/encode/httpx) but this library is still immature.

## TODO

- Debug TLS.
- Support proxies?

## Useful information

- https://aws.amazon.com/blogs/compute/authenticating-amazon-ecr-repositories-for-docker-cli-with-credential-helper/
- https://docs.microsoft.com/en-us/azure/container-registry/container-registry-faq
- https://cloud.google.com/container-registry/docs/advanced-authentication
