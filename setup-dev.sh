#!/bin/bash

PYVERSION=$1
ENV_DIR=$2
BASEDIR=`echo $0|sed 's|/.*||'`
EGGDIR=$BASEDIR/submodule/conveyor_bins/python
ENV_DIR=$4

if [ -z $ENV_DIR ]; then
    ENV_DIR=virtualenv
fi

if [ -z $PYVERSION ]
then
    PYVERSION=`python -c 'import sys; print ".".join(sys.version.split()[0].split(".")[0:2])'`
    echo "python version is $PYVERSION"
else
    PYBINVERSION=$PYVERSION
fi

UNAME=`uname`
MAC_DISTUTILS=/System/Library/Frameworks/Python.framework/Versions/$PYVERSION/lib/python$PYVERSION/distutils/__init__.py
if [ "$UNAME" == "Darwin" ]
then
    MACVER=`system_profiler SPSoftwareDataType |grep '^ *System Version:' |sed 's/.*OS X //' | sed 's/\(10\.[0-9]\)*.*$/\1/'`

    export PATH=$PATH:$BASEDIR/submodule/conveyor_bins/mac/$MACVER

    if [ ! -f $MAC_DISTUTILS ]
    then
	sudo cp mac/$PYVERSION/distutils/__init__.py $MAC_DISTUTILS
    fi
fi

if [ ! -d $ENV_DIR ]
then
	python$PYBINVERSION virtualenv.py  --extra-search-dir=$EGGDIR --never-download --system-site-packages $ENV_DIR
fi

. $ENV_DIR/bin/activate

echo "Upgrading setuptools"
easy_install -q  $EGGDIR/setuptools-0.6c11-py$PYVERSION.egg
echo "Installing modules"
easy_install -q $DIST_EGGS/mock-1.0.1-py$PYVERSION.egg
easy_install -q $DIST_EGGS/lockfile-0.9.1-py$PYVERSION.egg
easy_install -q $DIST_EGGS/python/python_daemon-1.6-py$PYVERSION.egg
easy_install -q $DIST_EGGS/argparse-1.2.1-py$PYVERSION.egg
easy_install -q $DIST_EGGS/unittest2-0.5.1-py$PYVERSION.egg
pip install -q --use-mirrors coverage doxypy mock unittest-xml-reporting

echo "Installing makerbot eggs"
easy_install -q $BASEDIR/../pyserial/pyserial-2.7_mb2.1-py$PYVERSION.egg
easy_install -q $BASEDIR/../s3g/makerbot_driver-0.1.1-py$PYVERSION.egg


