@ECHO OFF

SET CURDATE=%DATE:/=_%
SET CURDATEFULL=%CURDATE: =_%

SET CURTIME=%TIME:~0,-6%
SET CURTIMEFULL=%CURTIME::=_%

SET DATETIMEPREFIX=%CURDATEFULL%_%CURTIMEFULL%_

IF EXIST conveyord.avail.lock GOTO KILLSUCCEED
ECHO No such file or directory: conveyord.avail.lock
EXIT /B 1
GOTO DONE

:KILLSUCCEED

REM delete conveyord.avail.lock
DEL /F /Q conveyord.avail.lock

REM move conveyord.log to DATE_conveyord.log
MOVE /Y conveyord.log %DATETIMEPREFIX%conveyord.log


:DONE
REM There is no need to do this
REM IF EXIST virtualenv call virtualenv\Scripts\deactivate

EXIT /B 0
