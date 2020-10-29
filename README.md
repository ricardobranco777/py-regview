# regview

View the contents of a Docker Registry v2

[![Build Status](https://travis-ci.org/ricardobranco777/regview.svg?branch=master)](https://travis-ci.org/ricardobranco777/regview)

## Usage

```
regview [-h] [--insecure] [--no-trunc] [-u USERNAME] [-p PASSWORD] REGISTRY|IMAGE
  -h, --help            show this help message and exit
  -a, --all             Print information for all architectures
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
  -v, --verbose         Print image history if available
  -V, --version         Show version and exit
```

## Requirements

- Python 3.5+
- requests
- requests-toolbet
- python-dateutil
