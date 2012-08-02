from __future__ import (absolute_import, print_function, unicode_literals)

import sys
sys.path.insert(0,'src/main/python') # for testing only

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from conveyor.ipc import *

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


if __name__ == '__main__':
    unittest.main()


