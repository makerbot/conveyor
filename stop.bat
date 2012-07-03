@ECHO OFF

IF EXIST conveyord.pid GOTO KILLSUCCEED
ECHO No such file or directory: conveyord.pid
GOTO DONE

:KILLSUCCEED

REM UNIX kill $(cat conveyord.pid)
REM WINDOWS taskkill /pid (enumerate conveyrod.pid here)
FOR /F %PIDVAR in (conveyord.pid) DO TASKKILL %PIDVAR
IF EXIST conveyord.pid DEL /F /Q conveyord.pid
IF EXIST conveyord.socket DEL /F /Q conveyord.socket

:DONE
IF EXIST virtualenv virtualenv\Scripts\deactivate