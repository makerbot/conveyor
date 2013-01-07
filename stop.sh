#! /bin/sh
# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/stop.sh
#
# conveyor - Printing dispatch engine for 3D objects and their friends.
# Copyright © 2012 Matthew W. Samsonoff <matthew.samsonoff@makerbot.com>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# set -x

if [ -f conveyord.pid ]
then
    _pid=$(cat conveyord.pid)
else
    _pid=$(ps ax | grep -v grep | grep conveyor | cut -d ' ' -f 1)
fi

if [ -z "${_pid}" ]
then
    echo "conveyord is not running"
else
    kill "${_pid}"
    sleep 1
    if ps ax | grep -v grep | grep "${_pid}" > /dev/null 2>&1
    then
        kill -KILL "${_pid}"
    fi
fi
