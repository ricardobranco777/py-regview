test:
	@pylint regview
	@flake8 regview --ignore=E501

test-integration:
	@bash -n ./tests/integration.sh
	./tests/integration.sh
