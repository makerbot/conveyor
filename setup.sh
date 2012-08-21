#! /bin/sh

PYVERSION=$1

if [ -z $PYVERSION ]
then
    SERIALVERSION=`python --version 2>&1 | sed s/'Python '//|sed s/\.[0-9]*$//`
else
    SERIALVERSION=$PYVERSION
fi
 
if [ ! -d virtualenv/ ]
then
	python$PYVERSION virtualenv.py virtualenv
fi

. virtualenv/bin/activate
pip install -q --upgrade setuptools
pip install -q --use-mirrors coverage doxypy mock lockfile python-daemon unittest-xml-reporting argparse unittest2
easy_install -q submodule/conveyor_bins/pyserial-2.7_mb2.1-py$SERIALVERSION.egg

export PYTHONPATH=./submodule/s3g:./src/main/python:$PYTHONPATH
