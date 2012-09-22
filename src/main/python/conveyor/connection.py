# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/connection.py
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

from __future__ import (absolute_import, print_function, unicode_literals)

import errno
import logging
import os
import os.path
import select
import socket
import threading

import conveyor.stoppable

class Connection(conveyor.stoppable.Stoppable):
    def __init__(self):
        conveyor.stoppable.Stoppable.__init__(self)
        self._log = logging.getLogger(self.__class__.__name__)

    def read(self):
        raise NotImplementedError

    def write(self, data):
        raise NotImplementedError

class AbstractSocketConnection(Connection):
    def __init__(self, socket, address):
        Connection.__init__(self)
        self._condition = threading.Condition()
        self._stopped = False
        self._socket = socket
        self._address = address

    def stop(self):
        with self._condition:
            self._stopped = True

    def write(self, data):
        with self._condition:
            self._socket.sendall(data)

class _PosixSocketConnection(AbstractSocketConnection):
    def stop(self):
        AbstractSocketConnection.stop(self)
        # NOTE: use SHUT_RD instead of SHUT_RDWR or you will get annoying
        # 'Connection reset by peer' errors.
        try:
            self._socket.shutdown(socket.SHUT_RD)
            self._socket.close()
        except IOError as e:
            if errno.EBADF != e.args[0]:
                raise
            else:
                self._log.debug('handled exception', exc_info=True)

    def read(self):
        while True:
            with self._condition:
                stopped = self._stopped
            if stopped:
                return ''
            else:
                try:
                    data = self._socket.recv(4096)
                except IOError as e:
                    with self._condition:
                        stopped = self._stopped
                    if errno.EINTR != e.args[0] and not stopped:
                        raise
                    else:
                        # NOTE: too spammy
                        # self._log.debug('handled exception', exc_info=True)
                        continue
                else:
                    return data

class _Win32SocketConnection(AbstractSocketConnection):
    def read(self):
        while True:
            with self._condition:
                stopped = self._stopped
            if stopped:
                return ''
            else:
                rlist, wlist, xlist = select.select([self._socket], [], [], 1.0)
                if 0 != len(rlist):
                    try:
                        data = self._socket.recv(4096)
                    except IOError as e:
                        with self._condition:
                            stopped = self._stopped
                        if errno.EINTR != e.args[0] and not stopped:
                            raise
                        else:
                            # NOTE: too spammy
                            # self._log.debug('handled exception', exc_info=True)
                            continue
                    else:
                        return data

if 'nt' != os.name:
    SocketConnection = _PosixSocketConnection
else:
    SocketConnection = _Win32SocketConnection
