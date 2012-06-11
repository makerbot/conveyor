#! /bin/sh

if [ ! -d virtualenv/ ]
then
	virtualenv virtualenv
fi

. virtualenv/bin/activate
pip install coverage doxypy lockfile pyserial python-daemon unittest-xml-reporting
