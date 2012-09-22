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

class _AbstractSocketConnection(Connection):
    def __init__(self, socket, address):
        Connection.__init__(self)
        self._condition = threading.Condition()
        self._stopped = False
        self._socket = socket
        self._address = address

    def stop(self):
        self._stopped = True

    def write(self, data):
        with self._condition:
            self._socket.sendall(data)

if 'nt' != os.name:
    class _PosixSocketConnection(_AbstractSocketConnection):
        def stop(self):
            AbstractSocketConnection.stop(self)
            # NOTE: use SHUT_RD instead of SHUT_RDWR or you will get annoying
            # 'Connection reset by peer' errors.
            try:
                self._socket.shutdown(socket.SHUT_RD)
                self._socket.close()
            except IOError as e:
                # NOTE: the Python socket implementation throws EBADF when you
                # invoke methods on a closed socket.
                if errno.EBADF != e.args[0]:
                    raise
                else:
                    self._log.debug('handled exception', exc_info=True)

        def read(self):
            while True:
                if self._stopped:
                    return ''
                else:
                    try:
                        data = self._socket.recv(4096)
                    except IOError as e:
                        if errno.EINTR != e.args[0] and not self._stopped:
                            raise
                        else:
                            # NOTE: too spammy
                            # self._log.debug('handled exception', exc_info=True)
                            continue
                    else:
                        return data

    PipeConnection = _PosixSocketConnection
    SocketConnection = _PosixSocketConnection

else:
    import pywintypes
    import win32event
    import win32file
    import winerror

    class _Win32PipeConnection(Connection):
        @staticmethod
        def create(handle):
            buffer = win32file.AllocateReadBuffer(4096)
            overlapped_read = _Win32PipeConnection.createoverlapped()
            overlapped_write = _Win32PipeConnection.createoverlapped(0)
            connection = conveyor.connection.PipeConnection(
                handle, buffer, overlapped_read, overlapped_write)
            return connection

        @staticmethod
        def createoverlapped(flag=1):
            overlapped = pywintypes.OVERLAPPED()
            overlapped.hEvent = win32event.CreateEvent(None, flag, 0, None)
            return overlapped

        def __init__(self, handle, buffer, overlapped_read, overlapped_write):
            Connection.__init__(self)
            self._condition = threading.Condition()
            self._stopped = False
            self._handle = handle
            self._buffer = buffer
            self._overlapped_read = overlapped_read
            self._overlapped_write = overlapped_write

        def stop(self):
            self._stopped = True

        def read(self):
            try:
                hr, buffer = win32file.ReadFile(
                    self._handle, self._buffer, self._overlapped_read)
            except pywintypes.error as e:
                if winerror.ERROR_BROKEN_PIPE != e.winerror:
                    raise e
                else:
                    self._log.debug(
                        'handled exception', exc_info=True)
                    return ''
            else:
                if 0 == hr or winerror.ERROR_MORE_DATA == hr:
                    result = win32file.GetOverlappedResult(
                        self._handle, self._overlapped_read, True)
                    s = str(self._buffer[:result])
                    return s
                elif winerror.ERROR_IO_PENDING:
                    while True:
                        if self._stopped:
                            return ''
                        else:
                            value = win32event.WaitForSingleObject(
                                self._overlapped_read.hEvent, 1000)
                            if win32event.WAIT_OBJECT_0 == value:
                                try:
                                    result = win32file.GetOverlappedResult(
                                        self._handle, self._overlapped_read,
                                        True)
                                except pywintypes.error as e:
                                    if winerror.ERROR_BROKEN_PIPE != e.winerror:
                                        raise e
                                    else:
                                        self._log.debug(
                                            'handled exception', exc_info=True)
                                        return ''
                                else:
                                    s = str(self._buffer[:result])
                                    return s
                            elif win32event.WAIT_TIMEOUT == value:
                                continue
                            else:
                                raise ValueError(value)

        def write(self, data):
            with self._condition:
                s = str(data)
                win32file.WriteFile(self._handle, s, self._overlapped_write)
                win32event.WaitForSingleObject(
                    self._overlapped_write.hEvent, win32event.INFINITE)
                result = win32file.GetOverlappedResult(
                    self._handle, self._overlapped_write, True)

    class _Win32SocketConnection(_AbstractSocketConnection):
        def read(self):
            while True:
                if self._stopped:
                    return ''
                else:
                    rlist, wlist, xlist = select.select([self._socket], [], [], 1.0)
                    if 0 != len(rlist):
                        try:
                            data = self._socket.recv(4096)
                        except IOError as e:
                            if errno.EINTR != e.args[0] and not self._stopped:
                                raise
                            else:
                                # NOTE: too spammy
                                # self._log.debug('handled exception', exc_info=True)
                                continue
                        else:
                            return data

    PipeConnection = _Win32PipeConnection
    SocketConnection = _Win32SocketConnection
