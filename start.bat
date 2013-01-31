@ECHO OFF

CALL setup_conveyor_env.bat

SET CONVEYOR_SYNC_FILE=conveyor.pid

IF EXIST %CONVEYOR_SYNC_FILE% DEL /F /Q %CONVEYOR_SYNC_FILE%

ECHO Starting conveyor backend from start.bat

python conveyor_service.py -c conveyor.conf -l INFO

