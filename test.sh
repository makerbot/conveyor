#! /bin/sh

# set -x

_modules='
	conveyor
	conveyor.client
	conveyor.debug
	conveyor.enum
	conveyor.event
	conveyor.ipc
	conveyor.jsonrpc
	conveyor.log
	conveyor.main
	conveyor.process
	conveyor.recipe
	conveyor.server
	conveyor.stoppable
	conveyor.task
	conveyor.test
	conveyor.thing
	conveyor.toolpath
	conveyor.toolpath.skeinforge
	conveyor.visitor
'

if [ ! -d obj/ ]
then
	mkdir obj/
fi
PYTHONPATH=src/main/python/:submodule/s3g/:src/test/python
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=${PYTHONPATH} coverage erase  
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=${PYTHONPATH} coverage run --branch test.py -- -v ${_modules} pi_test_Address pi_test_thing pi_test_stoppable
_code=$?
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=${PYTHONPATH} coverage annotate -d obj/ --include 'src/main/python/*'
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=${PYTHONPATH} coverage html -d obj/ --include 'src/main/python/*' 
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=${PYTHONPATH} coverage xml -o obj/coverage.xml --include 'src/main/python/*'
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=${PYTHONPATH} coverage report -m --include 'src/main/python/*'
exit ${_code}
