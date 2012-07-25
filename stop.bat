@ECHO OFF

ECHO Stopping conveyor backend from stop.bat

REM UNIX kill $(cat conveyord.pid)
REM WINDOWS taskkill /pid (enumerate conveyrod.pid here)
REM net stop Conveyor
IF EXIST conveyord.pid DEL /F /Q conveyord.pid
IF EXIST conveyord.socket DEL /F /Q conveyord.socket


:DONE
IF EXIST virtualenv call virtualenv\Scripts\deactivate