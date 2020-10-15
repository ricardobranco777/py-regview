# regview

View the contents of a Docker Registry v2

[![Build Status](https://travis-ci.org/ricardobranco777/regview.svg?branch=master)](https://travis-ci.org/ricardobranco777/regview)

## Usage

```
regview [-h] [--insecure] [--no-trunc] [-u USERNAME] [-p PASSWORD] REGISTRY|IMAGE
  -h, --help            show this help message and exit
  -c CERT, --cert CERT  Client certificate filename (may contain unencrypted key)
  -k KEY, --key KEY     Client private key filename (unencrypted)
  -C CA_CERT, --ca-cert CA_CERT
                        CA certificate for server
  --debug               Enable debug
  --insecure            Allow insecure server connections
  --no-trunc            Don't truncate output
  -u USERNAME, --username USERNAME
                        Username for authentication
  -p PASSWORD, --password PASSWORD
                        Password for authentication
```

## Requirements

- Python 3.6+
- requests
- requests-toolbet
- python-dateutil
