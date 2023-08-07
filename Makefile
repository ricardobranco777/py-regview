FILES=*.py regview/*.py tests/*.py

.PHONY: all
all: flake8 pylint test:

.PHONY: flake8
flake8:
	@flake8 --ignore=E501 $(FILES)

.PHONY: pylint
pylint:
	@pylint --disable=line-too-long $(FILES)

.PHONY: test
test:
	@TZ=Europe/Berlin LC_ALL=en_US.UTF-8 python3 -m unittest tests/*.py
	@bash -n ./tests/e2e.sh


