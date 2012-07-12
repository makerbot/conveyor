#! /bin/sh

# set -x

./stop.sh
rm conveyord.log
python conveyor_service.py -l DEBUG -c conveyor.conf "${@}"

