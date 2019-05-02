#!/bin/bash
#
# Script to run Python 3 tests on Travis-CI.
#
# This file is generated by l2tdevtools update-dependencies.py, any dependency
# related changes should be made in dependencies.ini.

# Exit on error.
set -e;

python3 ./run_tests.py

if test -f tests/end-to-end.py;
then
	PYTHONPATH=. python3 ./tests/end-to-end.py --debug -c config/end-to-end.ini;
fi

python3 ./setup.py build

python3 ./setup.py sdist

python3 ./setup.py bdist

python3 ./setup.py install
