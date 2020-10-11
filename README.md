# regview

View the contents of a Docker Registry v2

[![Build Status](https://travis-ci.org/ricardobranco777/regview.svg?branch=master)](https://travis-ci.org/ricardobranco777/regview)

## Usage

```
regview [-h] [--insecure] [--no-trunc] [-u USERNAME] [-p PASSWORD] REGISTRY|IMAGE
  -h, --help            show this help message and exit
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
