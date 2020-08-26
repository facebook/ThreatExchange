all:
	echo >&2 "Must specify target."

test:
	tox

docs:
	tox -e docs

clean:
	rm -rf build/ dist/ *.egg-info/ .tox/
	rm -f .coverage
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

.PHONY: all test docs clean
