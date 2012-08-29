@ECHO OFF

SET CURDATE=%DATE:/=_%
SET CURDATENC=%CURDATE::=_%
SET CURDATEFULL=%CURDATENC: =_%

SET CURTIME=%TIME:~0,-6%
SET CURTIMENC=%CURTIME::=_%
SET CURTIMEFULL=%CURTIMENC: =%

SET DATETIMEPREFIX=%CURDATEFULL%_%CURTIMEFULL%_

IF EXIST conveyord.avail.lock GOTO KILLSUCCEED
ECHO No such file or directory: conveyord.avail.lock
GOTO MOVELOG

:KILLSUCCEED

REM delete conveyord.avail.lock
DEL /F /Q conveyord.avail.lock

:MOVELOG

REM move conveyord.log to DATE_conveyord.log
IF NOT EXIST conveyord.log GOTO FAILED
MOVE /Y conveyord.log %DATETIMEPREFIX%conveyord.log


:DONE
REM There is no need to do this
REM IF EXIST virtualenv call virtualenv\Scripts\deactivate

EXIT /B 0

:FAILED

EXIT /B 1

