@ECHO OFF

CALL setup.bat

ECHO Starting conveyor service from fd_start.bat
python conveyor_service.py -c conveyor-win32.conf

