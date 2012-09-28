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

import os
import socket

import conveyor.connection
import conveyor.listener

class Address(object):
    @staticmethod
    def parse(s):
        split = s.split(':', 1)
        if 'pipe' == split[0] or 'unix' == split[0]:
            address = PipeAddress._parse(s, split)
        elif 'tcp' == split[0]:
            address = TcpAddress._parse(s, split)
        else:
            raise UnknownProtocolException(s, split[0])
        return address

    def listen(self):
        raise NotImplementedError

    def connect(self):
        raise NotImplementedError

class PipeAddress(Address):
    @staticmethod
    def _parse(s, split):
        protocol = split[0]
        assert 'pipe' == protocol or 'unix' == protocol
        if 2 != len(split):
            raise MissingPathException(s)
        else:
            path = split[1]
            if 0 == len(path):
                raise MissingPathException(s)
            else:
                address = PipeAddress(path)
                return address

    def __init__(self, path):
        self._path = path

    def listen(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(self._path)
        os.chmod(self._path, 0666)
        s.listen(socket.SOMAXCONN)
        listener = conveyor.listener.PipeListener(s, self._path)
        return listener

    def connect(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self._path)
        connection = conveyor.connection.SocketConnection(s, None)
        return connection

class TcpAddress(Address):
    @staticmethod
    def _parse(s, split):
        protocol = split[0]
        assert 'tcp' == protocol
        if 2 != len(split):
            raise MissingHostException(s)
        else:
            hostport = split[1].split(':', 1)
            if 2 != len(hostport):
                raise MissingPortException(s)
            else:
                host = hostport[0]
                if 0 == len(host):
                    raise MissingHostException(s)
                else:
                    try:
                        port = int(hostport[1])
                    except ValueError:
                        raise InvalidPortException(s, hostport[1])
                    else:
                        address = TcpAddress(host, port)
                        return address

    def __init__(self, host, port):
        self._host = host
        self._port = port

    def listen(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self._host, self._port))
        s.listen(socket.SOMAXCONN)
        listener = conveyor.listener.TcpListener(s)
        return listener

    def connect(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self._host, self._port))
        connection = conveyor.connection.SocketConnection(s, None)
        return connection

class UnknownProtocolException(Exception):
    def __init__(self, value, protocol):
        Exception.__init__(self, value, protocol)
        self.value = value
        self.protocol = protocol

class MissingHostException(Exception):
    def __init__(self, value):
        Exception.__init__(self, value)
        self.value = value

class MissingPortException(Exception):
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
