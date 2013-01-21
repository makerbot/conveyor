# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/address.py
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

# Class Hierarchy of Addresses, Listeners, and Connections
# object
#   + Address
#   |   + _AbstractPipeAddress
#   |   |   - _PosixPipeAddress
#   |   |   - _Win32PipeAddress
#   |   - TcpAddress
#   + Listener
#   |   + _AbstractSocketListener
#   |   |   - _PosixPipeListener
#   |   |   + TcpListener
#   |   - _Win32PipeListener
#   + Connection
#       + _AbstractSocketConnection
#       |   - _PosixSocketConnection
#       |   - _Win32SocketConnection
#       - _Win32PipeConnection
#
# Table of Platform-specific Class Aliases
# +------------------+----------+------------------------+
# | Alias            | Platform | Class                  |
# +------------------+----------+------------------------+
# | PipeAddress      | posix    | _PosixPipeAddress      |
# | PipeAddress      | win32    | _Win32PipeAddress      |
# +------------------+----------+------------------------+
# | PipeListener     | posix    | _PosixPipeListener     |
# | PipeListener     | win32    | _Win32PipeListener     |
# +------------------+----------+------------------------+
# | PipeConnection   | posix    | _PosixSocketConnection |
# | PipeConnection   | win32    | _Win32PipeConnection   |
# +------------------+----------+------------------------+
# | SocketConnection | posix    | _PosixSocketConnection |
# | SocketConnection | win32    | _Win32SocketConnection |
# +------------------+----------+------------------------+
#
# Table of Addresses, Listeners, and Connections by Platform
# +------+----------+-------------------+---------------------+------------------------+
# | Kind | Platform | Address           | Listener            | Connection             |
# +------+----------+-------------------+---------------------+------------------------+
# | pipe | posix    | _PosixPipeAddress | _PosixPipeListener  | _PosixSocketConnection |
# | tcp  | posix    | TcpAddress        | TcpListener         | _PosixSocketConnection |
# | pipe | win32    | _Win32PipeAddress | _Win32PipeListener  | _Win32PipeConnection   |
# | tcp  | win32    | TcpAddress        | TcpListener         | _Win32SocketConnection |
# +------+----------+-------------------+---------------------+------------------------+

import os
import socket

import conveyor.connection
import conveyor.listener


class Address(object):
    """
    Base class for a addressable endpoint. This class can create the
    underlying sockets as needed based on the communication endpoint type.
    """

    @staticmethod
    def address_factory(addr):
        """ Constructs an Address object based on the passed string
        @param s Address string in the form pipe:$NAME or tcp:$URL:$PORT  
        @returns A proper Address-based object, based on type address type
        """
        split = addr.split(':', 1)
        if 'pipe' == split[0]:
            addressObj = _AbstractPipeAddress._factory(addr, split)
        elif 'tcp' == split[0]:
            addressObj = TcpAddress._factory(addr, split)
        else:
            raise UnknownProtocolException(addr, split[0])
        return addressObj


    def listen(self):
        raise NotImplementedError

    def connect(self):
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError


class _AbstractPipeAddress(Address):
    @staticmethod
    def _factory(s, split):
        protocol = split[0]
        if 'pipe' != protocol:
            raise UnknownProtocolException(protocol,'pipe')
        if 2 != len(split):
            raise MissingPathException(s)
        path = split[1]
        if 0 == len(path):
            raise MissingPathException(s)
        address = PipeAddress(path)
        return address

    def __init__(self, path):
        self._path = path

    def __str__(self):
        s = ':'.join(('pipe', self._path))
        return s


if 'nt' != os.name:
    class _PosixPipeAddress(_AbstractPipeAddress):
        def listen(self):
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.setblocking(True)
            s.bind(self._path)
            os.chmod(self._path, 0666)
            s.listen(socket.SOMAXCONN)
            listener = conveyor.listener.PipeListener(self._path, s)
            return listener

        def connect(self):
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.setblocking(True)
            s.connect(self._path)
            connection = conveyor.connection.SocketConnection(s, None)
            return connection

    PipeAddress = _PosixPipeAddress

else:
    import ctypes
    import ctypes.wintypes
    import conveyor.platform.win32 as win32

    class _Win32PipeAddress(_AbstractPipeAddress):
        def listen(self):
            listener = conveyor.listener.PipeListener(self._path)
            return listener

        def connect(self):
            handle = win32.CreateFileW(
                self._path,
                win32.GENERIC_READ | win32.GENERIC_WRITE,
                0,
                None,
                win32.OPEN_EXISTING,
                win32.FILE_FLAG_OVERLAPPED,
                None)
            lpMode = ctypes.wintypes.DWORD(win32.PIPE_READMODE_MESSAGE)
            win32.SetNamedPipeHandleState(handle, ctypes.byref(lpMode), None, None)
            connection = conveyor.connection.PipeConnection.create(handle)
            return connection

    PipeAddress = _Win32PipeAddress

class TcpAddress(Address):
    @staticmethod
    def _factory(s, split):
        protocol = split[0]
        if 'tcp' != protocol:
            raise UnknownProtocolException(protocol, 'tcp')
        if 2 != len(split):
            raise MissingHostException(s)
        hostport = split[1].split(':', 1)
        if 2 != len(hostport):
            raise MalformedUrlException(s)
        host = hostport[0]
        if 0 == len(host):
            raise MissingHostException(s)
        try:
            port = int(hostport[1])
        except ValueError:
            raise InvalidPortException(s, hostport[1])
        address = TcpAddress(host, port)
        return address

    def __init__(self, host, port):
        """
        @param host: name of computer we are connecting to
        @param port: number-id of port we are connecting to
        """
        self._host = host
        self._port = port

    def listen(self):
        """ creates a listener object connected to the specified port
        self._host must be a refer to the local host
        self._port must be a valid port
        """
        return self.listener_factory(self._port, self._host)

    @staticmethod
    def listener_factory(port, host='localhost'):
        """
        @param port must be an integer port number
        @param host must be a string reference to localhost
        @return a TcpListener object connected to the specified socket
        """     
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(socket.SOMAXCONN)
        listener = conveyor.listener.TcpListener(s)
        return listener

    def connect(self):
        """ creates a connection based on internal settings.
        @returns a SocketConnection object
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self._host, self._port))
        connection = conveyor.connection.SocketConnection(s, None)
        return connection

    def __str__(self):
        s = ':'.join(('tcp', self._host, str(self._port)))
        return s


class UnknownProtocolException(Exception):
    def __init__(self, value, protocol):
        Exception.__init__(self, value, protocol)
        self.value = value
        self.protocol = protocol

class MissingHostException(Exception):
    def __init__(self, value):
        Exception.__init__(self, value)
        self.value = value

class MalformedUrlException(Exception):
    """ Error when a tcp port specificion or url specification is invalid."""
    def __init__(self, value):
        Exception.__init__(self, value)
        self.value = value

class InvalidPortException(Exception):
    def __init__(self, value, port):
        Exception.__init__(self, value, port)
        self.value = value
        self.port = port

class MissingPathException(Exception):
    def __init__(self, value):
        Exception.__init__(self, value)
        self.value = value
