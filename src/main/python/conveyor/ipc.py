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
import socket
import tempfile
import threading

try:
    import unittest2 as unittest
except ImportError:
    import unittest

def getsocket(address):
    split = address.split(':', 1)
    if 'tcp' == split[0]:
        sock = _getsockettcp(address, split)
    elif 'unix' == split[0]:
        sock = _getsocketunix(address, split)
    else:
        raise UnknownProtocolException(address, split[0])
    return sock

def _getsockettcp(address, split):
    protocol = split[0]
    assert 'tcp' == protocol
    if 2 != len(split):
        raise MissingHostException(address)
    else:
        hostport = split[1].split(':', 1)
        if 2 != len(hostport):
            raise MissingPortException(address)
        else:
            host = hostport[0]
            if 0 == len(host):
                raise MissingHostException(address)
            else:
                try:
                    port = int(hostport[1])
                except ValueError:
                    raise InvalidPortException(address)
                else:
                    sock = TcpSocket(host, port)
                    return sock

def _getsocketunix(address, split):
    protocol = split[0]
    assert 'unix' == protocol
    if 2 != len(split):
        raise MissingPathException(address)
    else:
        path = split[1]
        if 0 == len(path):
            raise MissingPathException(address)
        else:
            sock = UnixSocket(path)
            return sock

class UnknownProtocolException(Exception):
    def __init__(self, address, protocol):
        Exception.__init__(self, address, protocol)
        self.address = address
        self.protocol = protocol

class MissingHostException(Exception):
    def __init__(self, address):
        Exception.__init__(self, address)
        self.address = address

class MissingPortException(Exception):
    def __init__(self, address):
        Exception.__init__(self, address)
        self.address = address

class InvalidPortException(Exception):
    def __init__(self, address):
        Exception.__init__(self, address)
        self.address = address

class MissingPathException(Exception):
    def __init__(self, address):
        Exception.__init__(self, address)
        self.address = address

class Socket(object):
    '''An abstract socket.'''

    def listen(self):
        raise NotImplementedError

    def connect(self):
        raise NotImplementedError

class TcpSocket(Socket):
    '''A TCP/IP socket.'''

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

class UnixSocket(Socket):
    '''A UNIX socket.'''

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

class _GetsocketTestCase(unittest.TestCase):
    def test_tcp(self):
        sock = getsocket('tcp:localhost:1234')
        self.assertIsInstance(sock, TcpSocket)
        self.assertEqual('localhost', sock._host)
        self.assertEqual(1234, sock._port)

    def test_unix(self):
        sock = getsocket('unix:/path')
        self.assertIsInstance(sock, UnixSocket)
        self.assertEqual('/path', sock._path)

    def test_UnknownProtocolException_0(self):
        with self.assertRaises(UnknownProtocolException) as cm:
            getsocket('a')
        self.assertEqual('a', cm.exception.address)
        self.assertEqual('a', cm.exception.protocol)

    def test_UnknownProtocolException_1(self):
        with self.assertRaises(UnknownProtocolException) as cm:
            getsocket('b:')
        self.assertEqual('b:', cm.exception.address)
        self.assertEqual('b', cm.exception.protocol)

    def test_UnknownProtocolException_2(self):
        with self.assertRaises(UnknownProtocolException) as cm:
            getsocket('c:d')
        self.assertEqual('c:d', cm.exception.address)
        self.assertEqual('c', cm.exception.protocol)

    def test_MissingHostException_0(self):
        with self.assertRaises(MissingHostException) as cm:
            getsocket('tcp')
        self.assertEqual('tcp', cm.exception.address)

    def test_MissingHostException_1(self):
        with self.assertRaises(MissingHostException) as cm:
            getsocket('tcp::1')
        self.assertEqual('tcp::1', cm.exception.address)

    def test_MissingPortException(self):
        with self.assertRaises(MissingPortException) as cm:
            getsocket('tcp:host')
        self.assertEqual('tcp:host', cm.exception.address)

    def test_InvalidPortException(self):
        with self.assertRaises(InvalidPortException) as cm:
            getsocket('tcp:host:port')
        self.assertEqual('tcp:host:port', cm.exception.address)

    def test_MissingPathException_0(self):
        with self.assertRaises(MissingPathException) as cm:
            getsocket('unix')
        self.assertEqual('unix', cm.exception.address)

    def test_MissingPathException_1(self):
        with self.assertRaises(MissingPathException) as cm:
            getsocket('unix:')
        self.assertEqual('unix:', cm.exception.address)

class _SocketTestCase(unittest.TestCase):
    def test_listen(self):
        sock = Socket()
        with self.assertRaises(NotImplementedError):
            sock.listen()

    def test_connect(self):
        sock = Socket()
        with self.assertRaises(NotImplementedError):
            sock.connect()

class _AbstractSocketTestCase(unittest.TestCase):
    def _getclientaddress(self, serveraddress, serversock):
        raise NotImplementedError

    def _test(self, serveraddress):
        server = getsocket(serveraddress)
        serversock = server.listen()
        try:
            serversock.settimeout(5)
            clientaddress = self._getclientaddress(serveraddress, serversock)
            def target():
                client = getsocket(clientaddress)
                clientsock = client.connect()
                clientsock.shutdown(socket.SHUT_RDWR)
            thread = threading.Thread(target=target)
            thread.start()
            sock, addr = serversock.accept()
        finally:
            serversock.shutdown(socket.SHUT_RDWR)

    def test__getclientaddress(self):
        with self.assertRaises(NotImplementedError):
            _AbstractSocketTestCase._getclientaddress(self, None, None)

class _TcpSocketTestCase(_AbstractSocketTestCase):
    def _getclientaddress(self, serveraddress, serversock):
        addr, port = serversock.getsockname()
        address = 'tcp:localhost:%d' % (port,)
        return address

    def test(self):
        self._test('tcp:localhost:0')

class _UnixSocketTestCase(_AbstractSocketTestCase):
    def _getclientaddress(self, serveraddress, serversock):
        return serveraddress

    def test(self):
        with tempfile.NamedTemporaryFile(delete=False) as fp:
            pass
        os.unlink(fp.name)
        address = 'unix:%s' % (fp.name,)
        self._test(address)
