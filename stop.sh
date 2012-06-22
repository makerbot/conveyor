#! /bin/sh

# set -x

if [ -f conveyord.pid ]
then
	kill $(cat conveyord.pid)
	if [ -e conveyord.pid ]
	then
		rm -f conveyord.pid
	fi
	if [ -e conveyord.socket ]
	then
		rm -f conveyord.socket
	fi
else
	echo no such file or directory: conveyord.pid
fi
