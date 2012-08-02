@ECHO OFF
ECHO Attempting to stop...
CALL stop.bat
REM stop.bat moves conveyord.log to <DATE>_<TIME>_conveyord.log
REM so there's no need to do this
REM ECHO Removing old log files...
REM IF EXIST conveyord.log DEL /F /Q conveyord.log
CALL start.bat
ECHO Started Server
