@ECHO OFF
SETLOCAL EnableDelayedExpansion
SET _MODULES=
SET _MODULES=!_MODULES! conveyor
SET _MODULES=!_MODULES! conveyor.client
SET _MODULES=!_MODULES! conveyor.debug
SET _MODULES=!_MODULES! conveyor.enum
SET _MODULES=!_MODULES! conveyor.event
SET _MODULES=!_MODULES! conveyor.ipc
SET _MODULES=!_MODULES! conveyor.jsonrpc
SET _MODULES=!_MODULES! conveyor.log
SET _MODULES=!_MODULES! conveyor.main
SET _MODULES=!_MODULES! conveyor.process
SET _MODULES=!_MODULES! conveyor.recipe
SET _MODULES=!_MODULES! conveyor.server
SET _MODULES=!_MODULES! conveyor.task
SET _MODULES=!_MODULES! conveyor.test
SET _MODULES=!_MODULES! conveyor.thing
SET _MODULES=!_MODULES! conveyor.toolpath
SET _MODULES=!_MODULES! conveyor.toolpath.skeinforge
SET _MODULES=!_MODULES! conveyor.visitor

SET PYTHONDONTWRITEBYTECODE=1
SET PYTHONPATH=src\main\python\..\..\..\submodule\s3g\

IF NOT EXIST obj MD obj

ECHO "exiting without testing for server-build reasons"
EXIT \B 0

CALL setup.bat

CALL start.bat

coverage run --branch test.py -- -v %_MODULES%
coverage annotate -d obj\ --include 'src\main\python\*'
coverage html -d obj\ --include 'src\main\python\*'
coverage xml -o obj\coverage.xml --include 'src\main\python\*'
coverage report --include 'src\main\python\*'

ENDLOCAL EnableDelayedExpansion

CALL stop.bat 
