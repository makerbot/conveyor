@ECHO OFF

CALL start.bat

ECHO Starting conveyor backend from start.bat
python conveyor_service.py -c conveyor-win32.conf

