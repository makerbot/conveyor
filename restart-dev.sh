#! /bin/sh

set -x

./stop-dev.py
rm -f *.log
rm -f conveyord.pid
rm -f conveyord.socket
./start-dev.py "${@}"
