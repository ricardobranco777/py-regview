test:
	@pylint regview
	@flake8 regview --ignore=E501
	@bash -n ./tests/integration.sh

test-integration:
	./tests/integration.sh
