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

class _AbstractSocketListener(Listener):
    def __init__(self, socket):
        Listener.__init__(self)
        self._stopped = False
        self._socket = socket

    def stop(self):
        self._stopped = True

    def accept(self):
        self._socket.settimeout(1.0)
        while True:
            if self._stopped:
                return None
            else:
                try:
                    sock, addr = self._socket.accept()
                except socket.timeout:
                    # NOTE: too spammy
                    # self._log.debug('handled exception', exc_info=True)
                    continue
                except IOError as e:
                    if errno.EINTR != e.args[0] and not self._stopped:
                        raise
                    else:
                        # NOTE: too spammy
                        # self._log.debug('handled exception', exc_info=True)
                        continue
                else:
                    connection = conveyor.connection.SocketConnection(sock, addr)
                    return connection

class TcpListener(_AbstractSocketListener):
    def cleanup(self):
        pass

if 'nt' != os.name:
    class _PosixPipeListener(_AbstractSocketListener):
        def __init__(self, socket, path):
            SocketListener.__init__(self, socket)
            self._path = path

        def cleanup(self):
            if os.path.exists(self._path):
                os.unlink(self._path)

    PipeListener = _PosixPipeListener

else:
    import win32event
    import win32file
    import win32pipe
    import winerror

    class _Win32PipeListener(Listener):
        def __init__(self, path):
            Listener.__init__(self)
            self._stopped = False
            self._path = path

        def stop(self):
            self._stopped = True

        def accept(self):
            handle = win32pipe.CreateNamedPipe(
                self._path,
                win32pipe.PIPE_ACCESS_DUPLEX | win32file.FILE_FLAG_OVERLAPPED,
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                win32pipe.PIPE_UNLIMITED_INSTANCES,
                4096,
                4096,
                0,
                None)
            overlapped = conveyor.connection.PipeConnection.createoverlapped()
            error = win32pipe.ConnectNamedPipe(handle, overlapped)
            if winerror.ERROR_IO_PENDING == error:
                while True:
                    if self._stopped:
                        return None
                    else:
                        value = win32event.WaitForSingleObject(overlapped.hEvent, 1000)
                        if win32event.WAIT_OBJECT_0 == value:
                            break
                        elif win32event.WAIT_TIMEOUT == value:
                            continue
                        else:
                            raise ValueError(value)
            elif winerror.ERROR_PIPE_CONNECTED != error:
                raise ValueError
            connection = conveyor.connection.PipeConnection.create(handle)
            return connection

        def cleanup(self):
            pass

    PipeListener = _Win32PipeListener
