@ECHO OFF
IF NOT EXIST virtualenv GOTO DIRNOTEXISTS

:DIREXISTS
call virtualenv\scripts\activate

SET PYTHONPATH=%CD%\submodule\s3g;%CD%\src\main\python;%PYTHONPATH%

REM EXIT /B 0

pip install -q --use-mirrors coverage doxypy mock unittest-xml-reporting pyserial
GOTO DONE


:DIRNOTEXISTS
python virtualenv.py virtualenv
GOTO DIREXISTS

:DONE
