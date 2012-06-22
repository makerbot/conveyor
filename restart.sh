#! /bin/sh

# set -x

./stop.sh
rm conveyord.log
./conveyord -c conveyor-user.conf
