#! /bin/sh

if [ ! -d virtualenv/ ]
then
	python virtualenv.py virtualenv
fi

. virtualenv/bin/activate
pip install --use-mirrors coverage doxypy lockfile pyserial python-daemon unittest-xml-reporting
