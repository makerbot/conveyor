@ECHO OFF
ECHO Attempting to stop...
CALL stop.bat
ECHO Removing old log files...
IF EXIST conveyord.log DEL /F /Q conveyord.log
IF EXIST virtualenv CALL virtualenv\Scripts\activate
ECHO Started Server - Press Ctrl + Pause to terminate
python conveyor_service.py -l DEBUG -c conveyor-user-server-win32.conf --nofork