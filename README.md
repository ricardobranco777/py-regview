# regview

View the contents of a Docker Registry v2

[![Build Status](https://travis-ci.org/ricardobranco777/regview.svg?branch=master)](https://travis-ci.org/ricardobranco777/regview)

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
