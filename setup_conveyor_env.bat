SET PYTHON=%1
SET DIST_EGGS=%2
SET MB_EGGS=%3
SET ENV_DIR=%4 

IF NOT "%DIST_EGGS%"=="" GOTO CONTINUE
SET DIST_EGGS=python
:CONTINUE

IF NOT "%MB_EGGS%"=="" GOTO CONTINUE
SET MB_EGGS=%DIST_EGGS%
:CONTINUE

IF NOT "%ENV_DIR%"==" " GOTO CONTINUE
SET ENV_DIR=virtualenv
:CONTINUE

IF EXIST %ENV_DIR% GOTO MODULES

%PYTHON% virtualenv.py --extra-search-dir=%DIST_EGGS% --never-download %ENV_DIR%

:MODULES
CALL virtualenv\Scripts\activate.bat

easy_install -q %DIST_EGGS%\mock-1.0.1-py2.7.egg
easy_install -q %DIST_EGGS%\lockfile-0.9.1-py2.7.egg
easy_install -q %DIST_EGGS%\python_daemon-1.6-py2.7.egg
easy_install -q %DIST_EGGS%\argparse-1.2.1-py2.7.egg
easy_install -q %DIST_EGGS%\unittest2-0.5.1-py2.7.egg


easy_install -q %MB_EGGS%\pyserial-2.7_mb2.1-py2.7.egg
easy_install -q %MB_EGGS%\makerbot_driver-0.1.1-py2.7.egg

IF NOT EXIST %MB_EGGS%\conveyor-2.0.0-py2.7.egg GOTO NOINSTALL
easy_install -q python\conveyor-2.0.0-py2.7.egg
:NOINSTALL

:DONE
