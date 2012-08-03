#! /bin/sh

if [ ! -d virtualenv/ ]
then
	python virtualenv.py virtualenv
	pip install --use-mirrors argparse coverage doxypy lockfile pyserial python-daemon unittest-xml-reporting
fi
. virtualenv/bin/activate
export PYTHONPATH=./:./submodule/s3g:$PYTHONPATH
