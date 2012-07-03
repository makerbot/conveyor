@ECHO OFF
CALL stop.bat
DEL /F /Q conveyord.log
CALL setup.bat
python src/main/python/conveyor/server/__main__.py -l DEBUG -c conveyor-user.conf