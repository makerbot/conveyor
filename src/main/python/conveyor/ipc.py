# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/ipc.py
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
import os.path
import socket
import struct
import tempfile
import threading


def getaddress(value):
    split = value.split(':', 1)
    if 'tcp' == split[0]:
        sock = _getaddresstcp(value, split)
    elif 'unix' == split[0]:
        sock = _getaddressunix(value, split)
    else:
        raise UnknownProtocolException(value, split[0])
    return sock

def _getaddresstcp(value, split):
    protocol = split[0]
    assert 'tcp' == protocol
    if 2 != len(split):
        raise MissingHostException(value)
    else:
        hostport = split[1].split(':', 1)
        if 2 != len(hostport):
            raise MissingPortException(value)
        else:
            host = hostport[0]
            if 0 == len(host):
                raise MissingHostException(value)
            else:
                try:
                    port = int(hostport[1])
                except ValueError:
                    raise InvalidPortException(value, hostport[1])
                else:
                    sock = TcpAddress(host, port)
                    return sock

def _getaddressunix(value, split):
    protocol = split[0]
    assert 'unix' == protocol
    if 2 != len(split):
        raise MissingPathException(value)
    else:
        path = split[1]
        if 0 == len(path):
            raise MissingPathException(value)
        else:
            sock = UnixAddress(path)
            return sock

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

class Address(object):
    '''An abstract socket address.'''

    def listen(self):
        raise NotImplementedError

    def connect(self):
        raise NotImplementedError

    def cleanup(self):
        raise NotImplementedError

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()
        return False

class TcpAddress(Address):
    '''A TCP/IP socket address.'''

    def __init__(self, host, port):
        self._host = host
        self._port = port

    def listen(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self._host, self._port))
        s.listen(socket.SOMAXCONN)
        return s

    def connect(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self._host, self._port))
        return s

    def cleanup(self):
        pass

class UnixAddress(Address):
    '''A UNIX socket address.'''

    def __init__(self, path):
        self._path = path

    def listen(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(self._path)
        s.listen(socket.SOMAXCONN)
        return s

    def connect(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self._path)
        return s

    def cleanup(self):
        if os.path.exists(self._path):
            os.unlink(self._path)


