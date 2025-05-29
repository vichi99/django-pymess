.PHONY: install-dev test

install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

test:
	coverage run -m pytest
	coverage report
	coverage lcov 