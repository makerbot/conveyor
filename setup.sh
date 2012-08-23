#!/bin/bash

PYVERSION=$1
BASEDIR=`echo $0|sed 's|/.*||'`

if [ -z $PYVERSION ]
then
    PYVERSION=`python --version 2>&1 | sed s/'Python '//|sed s/\.[0-9]*$//`
    echo "python version is $PYVERSION"
else
    PYBINVERSION=$PYVERSION
fi

UNAME=`uname`
MAC_DISTUTILS=/System/Library/Frameworks/Python.framework/Versions/$PYVERSION/lib/python$PYVERSION/distutils/__init__.py
if [ "$UNAME" == "Darwin" ]
then
    MACVER=`system_profiler SPSoftwareDataType |grep '^ *System Version:' |sed 's/.*Mac OS X //' | sed 's/\.[^.]*$//'`

    export PATH=$PATH:$BASEDIR/submodule/conveyor_bins/mac/$MACVER

    if [ ! -f $MAC_DISTUTILS ]
    then
	sudo cp mac/$PYVERSION/distutils/__init__.py $MAC_DISTUTILS
    fi
fi

PYVERSION=$1

if [ -z $PYVERSION ]
then
    SERIALVERSION=`python --version 2>&1 | sed s/'Python '//|sed s/\.[0-9]*$//`
else
    SERIALVERSION=$PYVERSION
fi
 
if [ ! -d virtualenv/ ]
then
	python$PYBINVERSION virtualenv.py virtualenv
fi

. virtualenv/bin/activate
echo "Upgrading setuptools"
pip install -q --upgrade setuptools
echo "Installing modules"
pip install -q --use-mirrors coverage doxypy mock lockfile python-daemon unittest-xml-reporting argparse unittest2
echo "Installing pyserial egg"
easy_install -q submodule/conveyor_bins/pyserial-2.7_mb2.1-py$PYVERSION.egg

export PYTHONPATH=./submodule/s3g:./src/main/python:$PYTHONPATH
