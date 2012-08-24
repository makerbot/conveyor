#! /bin/sh

# set -x

#instate a virtualenv if needed
. ./stop.sh
. ./start.sh
mv conveyord.log "conveyord_`date +%Y%m%d_%H`_.log"
python conveyor_service.py -l DEBUG -c conveyor-dev.conf "${@}"

