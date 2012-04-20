#! /bin/sh

if [ ! -d virtualenv/ ]
then
	virtualenv virtualenv
fi

. virtualenv/bin/activate
pip install coverage doxypy unittest-xml-reporting
