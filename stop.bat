@ECHO OFF

SET CURDATE=%DATE:/=_%
SET CURDATENC=%CURDATE::=_%
SET CURDATEFULL=%CURDATENC: =_%

SET CURTIME=%TIME:~0,-6%
SET CURTIMENC=%CURTIME::=_%
SET CURTIMEFULL=%CURTIMENC: =%

SET DATETIMEPREFIX=%CURDATEFULL%_%CURTIMEFULL%_

SET CONVEYOR_SYNC_FILE=conveyor.pid

IF EXIST %CONVEYOR_SYNC_FILE% GOTO KILLSUCCEED
ECHO No such file or directory: %CONVEYOR_SYNC_FILE%
GOTO MOVELOG

:KILLSUCCEED

REM stop conveyor process
FOR /F %%A IN (%CONVEYOR_SYNC_FILE%) DO TASKKILL /PID %%A /F /T
REM delete the sync file
REM don't delete, start.bat does this
REM IF NOT ERRORLEVEL 0 DEL /F /Q %CONVEYOR_SYNC_FILE%

:MOVELOG

REM move conveyord.log to DATE_conveyord.log
IF NOT EXIST conveyord.log GOTO FAILEDLOG
MOVE /Y conveyord.log %DATETIMEPREFIX%conveyord.log


:DONE
REM There is no need to do this
REM IF EXIST virtualenv call virtualenv\Scripts\deactivate

EXIT /B 0

:FAILEDLOG
ECHO No such file or directory: conveyord.log

EXIT /B 0

