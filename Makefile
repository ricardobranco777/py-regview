test:
	@pylint regview
	@flake8 regview --ignore=E501

test-integration:
	./tests/integration.sh
