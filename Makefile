test:
	@pylint regview --disable=line-too-long
	@flake8 regview --ignore=E501
