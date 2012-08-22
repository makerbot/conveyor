#! /bin/sh

if [ ! -d virtualenv/ ]
then
	python virtualenv.py virtualenv
fi

. virtualenv/bin/activate
pip install -q --use-mirrors coverage doxypy mock lockfile python-daemon unittest-xml-reporting argparse
easy_install -q submodule/conveyor_bins/pyserial-2.7_mb2.1-py2.7.egg

export PYTHONPATH=./submodule/s3g:./src/main/python:$PYTHONPATH
