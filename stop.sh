#! /bin/sh

# set -x

#shutdown processes
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

#deactivate our virtualenv
if [ ! -z $VIRTUAL_ENV ] ; then
	echo "Deactivating Virtual at $VIRTUAL_ENV"
	deactivate
fi

