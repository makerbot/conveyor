@ECHO OFF
IF NOT EXIST virtualenv GOTO DIRNOTEXISTS

:DIREXISTS
CALL virtualenv\Scripts\activate.bat

SET PYTHONPATH=%CD%\submodule\s3g;%CD%\src\main\python;%PYTHONPATH%

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

SET PYTHON=%1

SET SEARCH_DIR=submodule/conveyor_bins/python
IF NOT EXIST %SEARCH_DIR% SET SEARCH_DIR=python

%PYTHON% virtualenv.py --extra-search-dir=%SEARCH_DIR% --never-download virtualenv
GOTO DIREXISTS

:DONE
