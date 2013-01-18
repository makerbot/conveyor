@ECHO OFF
IF NOT EXIST virtualenv GOTO DIRNOTEXISTS

:DIREXISTS
CALL virtualenv\scripts\activate

SET PYTHONPATH=%CD%\submodule\s3g;%CD%\src\main\python;%PYTHONPATH%

REM EXIT /B 0

easy_install -q python\pyserial-2.7_mb2.1-py2.7.egg
easy_install -q python\mock-1.0.1-py2.7.egg
easy_install -q python\lockfile-0.9.1-py2.7.egg
easy_install -q python\python_daemon-1.6-py2.7.egg
easy_install -q python\argparse-1.2.1-py2.7.egg
easy_install -q python\unittest2-0.5.1-py2.7.egg
easy_install -q python\pyserial-2.7_mb2.1-py2.7.egg
easy_install -q python\makerbot_driver-0.1.1-py2.7.egg
easy_install -q python\conveyor-2.0.0-py2.7.egg

GOTO DONE


:DIRNOTEXISTS

set PYTHON=%1

%PYTHON% virtualenv.py --extra-search-dir=submodule/conveyor_bins/python --never-download virtualenv
GOTO DIREXISTS

:DONE
