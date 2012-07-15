@ECHO OFF
IF NOT EXIST virtualenv GOTO DIRNOTEXISTS

:DIREXISTS
call virtualenv\scripts\activate

pip install --use-mirrors argparse coverage doxypy lockfile pyserial unittest-xml-reporting
GOTO DONE

:DIRNOTEXISTS
python virtualenv.py virtualenv
GOTO DIREXISTS

:DONE
