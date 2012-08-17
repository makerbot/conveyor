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

try:
    import unittest2 as unittest
except ImportError:
    import unittest

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
        os.chmod(self._path, 0666)
        s.listen(socket.SOMAXCONN)
        return s

    def connect(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self._path)
        return s

    def cleanup(self):
        if os.path.exists(self._path):
            os.unlink(self._path)

class _GetaddressTestCase(unittest.TestCase):
    def test_tcp(self):
        '''Test getaddress for a TCP socket address.'''

        sock = getaddress('tcp:localhost:1234')
        self.assertIsInstance(sock, TcpAddress)
        self.assertEqual('localhost', sock._host)
        self.assertEqual(1234, sock._port)

    def test_unix(self):
        '''Test getaddress for a UNIX socket address.'''

        sock = getaddress('unix:/path')
        self.assertIsInstance(sock, UnixAddress)
        self.assertEqual('/path', sock._path)

    def test_UnknownProtocolException_0(self):
        '''Test that getaddress throws an UnknownProtocolException when the
        address has an unknown protocol and no colon.

        '''

        with self.assertRaises(UnknownProtocolException) as cm:
            getaddress('a')
        self.assertEqual('a', cm.exception.value)
        self.assertEqual('a', cm.exception.protocol)

    def test_UnknownProtocolException_1(self):
        '''Test that getaddress throws an UnknownProtocolException when the
        address has an unknown protocol, a single colon, and it is the last
        character.

        '''

        with self.assertRaises(UnknownProtocolException) as cm:
            getaddress('b:')
        self.assertEqual('b:', cm.exception.value)
        self.assertEqual('b', cm.exception.protocol)

    def test_UnknownProtocolException_2(self):
        '''Test that getaddress throws an UnknownProtocolException when the
        address has an unknown protocol.

        '''

        with self.assertRaises(UnknownProtocolException) as cm:
            getaddress('c:d')
        self.assertEqual('c:d', cm.exception.value)
        self.assertEqual('c', cm.exception.protocol)

    def test_MissingHostException_0(self):
        '''Test that getaddress throws a MissingHostException when only the
        protocol is specified.

        '''

        with self.assertRaises(MissingHostException) as cm:
            getaddress('tcp')
        self.assertEqual('tcp', cm.exception.value)

    def test_MissingHostException_1(self):
        '''Test that getaddress throws a MissingHostException when no host is
        specified.

        '''

        with self.assertRaises(MissingHostException) as cm:
            getaddress('tcp::1')
        self.assertEqual('tcp::1', cm.exception.value)

    def test_MissingPortException(self):
        '''Test that getaddress throws a MissingPortException when no port is
        specified.

        '''

        with self.assertRaises(MissingPortException) as cm:
            getaddress('tcp:host')
        self.assertEqual('tcp:host', cm.exception.value)

    def test_InvalidPortException(self):
        '''Test that getaddress throws an InvalidPortException when an invalid
        port is specified.

        '''

        with self.assertRaises(InvalidPortException) as cm:
            getaddress('tcp:host:port')
        self.assertEqual('tcp:host:port', cm.exception.value)
        self.assertEqual('port', cm.exception.port)

    def test_MissingPathException_0(self):
        '''Test that getaddress throws a MissingPathException when the UNIX
        address has no colon.

        '''

        with self.assertRaises(MissingPathException) as cm:
            getaddress('unix')
        self.assertEqual('unix', cm.exception.value)

    def test_MissingPathException_1(self):
        '''Test that getaddress throws a MissingPathException when the UNIX
        path has a single colon and it is the last character.

        '''

        with self.assertRaises(MissingPathException) as cm:
            getaddress('unix:')
        self.assertEqual('unix:', cm.exception.value)

class _AddressTestCase(unittest.TestCase):
    def test_listen(self):
        '''Test that the listen method throws a NotImplementedError.'''

        sock = Address()
        with self.assertRaises(NotImplementedError):
            sock.listen()

    def test_connect(self):
        '''Test that the connect method throws an NotImplementedError.'''

        sock = Address()
        with self.assertRaises(NotImplementedError):
            sock.connect()

    def test_cleanup(self):
        '''Test that the cleanup method throws a NotImplementedError.'''

        sock = Address()
        with self.assertRaises(NotImplementedError):
            sock.cleanup()

    def test_with(self):
        '''Test that the address throws a NotImplementedError when it is used
        in a with statement.

        '''

        sock = Address()
        with self.assertRaises(NotImplementedError):
            with sock:
                pass

class _AbstractAddressTestCase(unittest.TestCase):
    def _getclientvalue(self, servervalue, serversock):
        raise NotImplementedError

    @unittest.skip("-----This test is broken on mac------")
    def _test(self, servervalue):
        server = getaddress(servervalue)
        serversock = server.listen()
        try:
            serversock.settimeout(5)
            clientvalue = self._getclientvalue(servervalue, serversock)
            def target():
                client = getaddress(clientvalue)
                clientsock = client.connect()
                clientsock.shutdown(socket.SHUT_RDWR)
                clientsock.close()
            thread = threading.Thread(target=target)
            thread.start()
            sock, addr = serversock.accept()
        finally:
            serversock.shutdown(socket.SHUT_RDWR)
            serversock.close()

    def test__getclientvalue(self):
        with self.assertRaises(NotImplementedError):
            _AbstractAddressTestCase._getclientvalue(self, None, None)

class _TcpAddressTestCase(_AbstractAddressTestCase):
    def _getclientvalue(self, servervalue, serversock):
        addr, port = serversock.getsockname()
        value = 'tcp:localhost:%d' % (port,)
        return value

    def test(self):
        '''Test connecting to a valid TCP address.'''

        self._test('tcp:localhost:0')

    def test_cleanup(self):
        '''Test cleanup for a TCP address (which does nothing).'''

        address = getaddress('tcp:localhost:0')
        with address:
            pass

class _UnixAddressTestCase(_AbstractAddressTestCase):
    def _getclientvalue(self, servervalue, serversock):
        return servervalue

    def test(self):
        '''Test connecting to a valid UNIX address.'''

        with tempfile.NamedTemporaryFile(delete=False) as fp:
            pass
        os.unlink(fp.name)
        value = 'unix:%s' % (fp.name,)
        self._test(value)

    def test_cleanup(self):
        '''Test cleanup for a UNIX address.'''

        with tempfile.NamedTemporaryFile(delete=False) as fp:
            pass
        os.unlink(fp.name)
        value = 'unix:%s' % (fp.name,)
        address = getaddress(value)
        with address:
            self.assertFalse(os.path.exists(fp.name))
        address.listen()
        with address:
            self.assertTrue(os.path.exists(fp.name))
        self.assertFalse(os.path.exists(fp.name))
