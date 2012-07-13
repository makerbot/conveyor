@ECHO OFF
CALL stop.bat
IF EXIST conveyord.log DEL /F /Q conveyord.log
IF EXIST virtualenv CALL virtualenv\Scripts\activate
python conveyor_service.py -l DEBUG -c conveyor-user-server-win32.conf --nofork
