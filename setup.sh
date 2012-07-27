#! /bin/sh

if [ ! -d virtualenv/ ]
then
	python virtualenv.py virtualenv
fi

. virtualenv/bin/activate
pip install --use-mirrors argparse coverage doxypy lockfile pyserial python-daemon unittest-xml-reporting
export PYTHONPATH=./submodule/s3g:./src/main/python:$PYTHONPATH
