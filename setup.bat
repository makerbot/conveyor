@ECHO OFF
IF NOT EXIST virtualenv GOTO DIRNOTEXISTS

:DIREXISTS
CALL virtualenv\scripts\activate

pip install -q --use-mirrors argparse coverage doxypy lockfile mock pyserial unittest-xml-reporting
easy_install submodules/conveyor_bins/pyserial-2.7_mb-py2.7.egg
GOTO DONE

:DIRNOTEXISTS
python virtualenv.py virtualenv
GOTO DIREXISTS

:DONE
