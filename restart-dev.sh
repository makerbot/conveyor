#! /bin/sh

set -x
set -e

./stop-dev.py
rm -f *.log
./start-dev.py "${@}"
