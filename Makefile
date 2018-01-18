PYTHONPATH=$(CURDIR)

.PHONY: all

all: test

test:
	tox

flake:
	tox -e flake

install:
	python setup.py install

build:
	python -m pip install tox
	python -m pip install virtualenv

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete

egg:
	python3.4 setup.py bdist_egg
