@ECHO OFF

ECHO Restarting conveyor windows service from fd_restart.bat
net stop Conveyor
net start Conveyor

