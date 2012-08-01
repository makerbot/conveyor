#! /bin/sh

if [ ! -d virtualenv/ ]
then
	python virtualenv.py virtualenv
fi

. virtualenv/bin/activate
pip install --use-mirrors argparse coverage doxypy mock lockfile python-daemon unittest-xml-reporting unittest2
easy_install submodule/conveyor_bins/pyserial-2.7_mb-py2.7.egg
export PYTHONPATH=./submodule/s3g:./src/main/python:$PYTHONPATH
