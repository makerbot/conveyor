#!/bin/bash

PYVERSION=$1
BASEDIR=`echo $0|sed 's|/.*||'`

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

if [ ! -d virtualenv/ ]
then
	python$PYBINVERSION virtualenv.py  --extra-search-dir=submodule/conveyor_bins/python --never-download virtualenv
fi

. virtualenv/bin/activate

echo "Upgrading setuptools"
easy_install -q submodule/conveyor_bins/python/setuptools-0.6c11-py$PYVERSION.egg
echo "Installing modules"
easy_install -q submodule/conveyor_bins/python/mock-1.0.1-py$PYVERSION.egg
easy_install -q submodule/conveyor_bins/python/lockfile-0.9.1-py$PYVERSION.egg
easy_install -q submodule/conveyor_bins/python/python_daemon-1.6-py$PYVERSION.egg
easy_install -q submodule/conveyor_bins/python/argparse-1.2.1-py$PYVERSION.egg
easy_install -q submodule/conveyor_bins/python/unittest2-0.5.1-py$PYVERSION.egg
easy_install -q submodule/conveyor_bins/python/pyserial-2.7_mb2.1-py$PYVERSION.egg

