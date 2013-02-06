#!/bin/bash

PYVERSION=$1
DIST_EGGS=$2
MB_EGGS=$3
ENV_DIR=$4

if [ -z $DIST_EGGS ]; then
    DIST_EGGS=`echo $0|sed 's|/.*||'`/python
fi

if [ -z $MB_EGGS ]; then
    MB_EGGS=$DIST_EGGS
fi

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

    export PATH=$PATH:$BASEDIR//mac/$MACVER

    if [ ! -f $MAC_DISTUTILS ]
    then
	sudo cp mac/$PYVERSION/distutils/__init__.py $MAC_DISTUTILS
    fi
fi

if [ ! -d $ENV_DIR ]
then
	python$PYBINVERSION virtualenv.py --extra-search-dir=$DIST_EGGS --never-download --system-site-packages $ENV_DIR
fi

. virtualenv/bin/activate

echo "Upgrading setuptools"
easy_install -q  $DIST_EGGS/setuptools-0.6c11-py$PYVERSION.egg
echo "Installing modules"
easy_install -q $DIST_EGGS/mock-1.0.1-py$PYVERSION.egg
easy_install -q $DIST_EGGS/lockfile-0.9.1-py$PYVERSION.egg
easy_install -q $DIST_EGGS/python_daemon-1.6-py$PYVERSION.egg
easy_install -q $DIST_EGGS/argparse-1.2.1-py$PYVERSION.egg
easy_install -q $DIST_EGGS/unittest2-0.5.1-py$PYVERSION.egg
easy_install -q $MB_EGGS/pyserial-2.7_mb2.1-py$PYVERSION.egg
easy_install -q $MB_EGGS/makerbot_driver-0.1.1-py$PYVERSION.egg

if [ -f $MB_EGGS/conveyor-2.0.0-py$PYVERSION.egg ]; then
    easy_install -q $MB_EGGS/conveyor-2.0.0-py$PYVERSION.egg
fi
