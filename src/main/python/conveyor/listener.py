# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/listener.py
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
import socket
import threading

import conveyor.connection
import conveyor.stoppable

class Listener(conveyor.stoppable.Stoppable):
    def __init__(self):
        conveyor.stoppable.Stoppable.__init__(self)
        self._log = logging.getLogger(self.__class__.__name__)

    def accept(self):
        raise NotImplementedError

    def cleanup(self):
        raise NotImplementedError

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()
        return False

class SocketListener(Listener):
    def __init__(self, socket):
        Listener.__init__(self)
        self._condition = threading.Condition()
        self._stopped = False
        self._socket = socket

    def stop(self):
        with self._condition:
            self._stopped = True

    def accept(self):
        self._socket.settimeout(1.0)
        while True:
            with self._condition:
                stopped = self._stopped
            if stopped:
                return None
            else:
                try:
                    sock, addr = self._socket.accept()
                except socket.timeout:
                    # NOTE: too spammy
                    # self._log.debug('handled exception', exc_info=True)
                    continue
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
                    connection = conveyor.connection.SocketConnection(sock, addr)
                    return connection

class PipeListener(SocketListener):
    def __init__(self, socket, path):
        SocketListener.__init__(self, socket)
        self._path = path

    def cleanup(self):
        if os.path.exists(self._path):
            os.unlink(self._path)

class TcpListener(SocketListener):
    def cleanup(self):
        pass
