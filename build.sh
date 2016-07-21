#!/bin/bash

python setup.py sdist --formats=gztar,zip
python setup.py bdist --format=gztar,zip
python setup.py bdist_wheel
python setup.py bdist_egg
