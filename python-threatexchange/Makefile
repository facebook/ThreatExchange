all:
	echo >&2 "Must specify target."

package:
	python3 -m build

local_install:
	python3 -m pip install -e .[all]

test:
	python3 -m pytest

push:
	python3 -m twine upload --repository testpypi dist/*

clean:
	rm -rf build/ dist/ *.egg-info/
	rm -f .coverage
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete


.PHONY: all clean package local_install test push clean
