test:
	@pylint regview setup.py _regview/*.py tests/*.py
	@flake8 regview setup.py _regview/*.py tests/*.py --ignore=E501
	@TZ=Europe/Berlin LC_ALL=en_US.UTF-8 python3 -m unittest tests/*.py
	@bash -n ./tests/integration.sh

test-integration:
	./tests/integration.sh

upload-pypi:
	@python3 setup.py sdist bdist_wheel
	@python3 -m twine upload dist/*

clean:
	@rm -rf dist/ build/ *.egg-info
