test:
	@pylint regview setup.py _regview/*.py
	@flake8 regview setup.py _regview/*.py --ignore=E501
	@bash -n ./tests/integration.sh

test-integration:
	./tests/integration.sh

upload-pypi:
	@python3 setup.py sdist bdist_wheel
	@python3 -m twine upload dist/*

clean:
	@rm -rf dist/ build/ *.egg-info
