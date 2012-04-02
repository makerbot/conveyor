#! /bin/sh

# set -x

_modules='
	conveyor.async
	conveyor.async.glib
	conveyor.enum
	conveyor.event
	conveyor.printer
	conveyor.printer.dbus
	conveyor.toolpathgenerator
	conveyor.toolpathgenerator.dbus
'
_files='
	src/main/python/conveyor/async/__init__.py
	src/main/python/conveyor/async/glib.py
	src/main/python/conveyor/enum.py
	src/main/python/conveyor/event.py
	src/main/python/conveyor/printer/__init__.py
	src/main/python/conveyor/printer/dbus.py
	src/main/python/conveyor/toolpathgenerator/__init__.py
	src/main/python/conveyor/toolpathgenerator/dbus.py
'

if [ ! -d obj/ ]
then
	mkdir obj/
fi

env PYTHONPATH=src/main/python/ python -m coverage run --branch -m unittest ${_modules}
env PYTHONPATH=src/main/python/ python -m coverage annotate -d obj/ ${_files}
env PYTHONPATH=src/main/python/ python -m coverage html -d obj/ ${_files}
env PYTHONPATH=src/main/python/ python -m coverage xml -o obj/coverage.xml ${_files}
env PYTHONPATH=src/main/python/ python -m coverage report ${_files}
