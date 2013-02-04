@ECHO OFF

SET CONVEYOR_SYNC_FILE=conveyor.pid

IF EXIST %CONVEYOR_SYNC_FILE% DEL /F /Q %CONVEYOR_SYNC_FILE%

ECHO Starting conveyor backend from start.bat

virtualenv\Scripts\python.exe -m conveyor.server -c conveyor.conf

