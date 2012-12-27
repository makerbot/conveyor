@ECHO OFF
IF NOT EXIST virtualenv GOTO DIRNOTEXISTS

:DIREXISTS
CALL virtualenv\scripts\activate

SET PYTHONPATH=%CD%\submodule\s3g;%CD%\src\main\python;%PYTHONPATH%

REM EXIT /B 0

easy_install -q submodule\conveyor_bins\pyserial-2.7_mb2.1-py2.7.egg
easy_install -q submodule\conveyor_bins\mock-1.0.1-py2.7.egg
easy_install -q submodule\conveyor_bins\lockfile-0.9.1-py2.7.egg
easy_install -q submodule\conveyor_bins\python_daemon-1.6-py2.7.egg
easy_install -q submodule\conveyor_bins\argparse-1.2.1-py2.7.egg
easy_install -q submodule\conveyor_bins\unittest2-0.5.1-py2.7.egg
easy_install -q submodule\conveyor_bins\pyserial-2.7_mb2.1-py2.7.egg

GOTO DONE


:DIRNOTEXISTS

IF "%1" == "" GOTO DEFAULTPY
set PYTHON=%1
GOTO VIRTUALENV

:DEFAULTPY
set PYTHON=python

:VIRTUALENV
%PYTHON% virtualenv.py --extra-search-dir=submodule/conveyor_bins/python --never-download virtualenv
GOTO DIREXISTS

:DONE
