@ECHO OFF
ECHO Attempting to stop...
CALL stop.bat
ECHO Removing old log files...
IF EXIST conveyord.log DEL /F /Q conveyord.log
CALL start.bat
ECHO Started Server
