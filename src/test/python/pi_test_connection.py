import unittest

import sys
import os

#override sys.path for testing only 
sys.path.insert(0,'./src/main/python')
import conveyor
import conveyor.connection

import socket
import mock
import errno

class  TestConnection(unittest.TestCase):


	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_base_unimplemented(self):
		aObj = conveyor.connection.Connection()
		
		# as template, these should throw 'NotImplemented'
		with self.assertRaises(NotImplementedError):
			data = aObj.read()

		with self.assertRaises(NotImplementedError):
			aObj.write('data')

class Test_AbstractSocketConnection(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_constructor(self):
		fakeSock = mock.Mock(socket.socket)		
		x = conveyor.connection._AbstractSocketConnection(fakeSock,'address')
		x.write('data')

	def test_write_exceptions_unnahdled(self):
		# test handling a BADF exception
		def fake_sendall_ret_badf(*arg,**kwargs):
			raise IOError(errno.EBADF,"fake BADF error")
		fakeSock = mock.Mock(socket.socket)		
		fakeSock.sendall = fake_sendall_ret_badf
		x = conveyor.connection._AbstractSocketConnection(fakeSock,'address')

		with self.assertRaises(conveyor.connection.ConnectionWriteException):
			x.write('data')

		# test handling a EPIPE exception
		def fake_sendall_ret_epipe(*arg,**kwargs):
			raise IOError(errno.EPIPE,"fake EPIPE error")
		fakeSock2 = mock.Mock(socket.socket)		
		fakeSock2.sendall = fake_sendall_ret_epipe 
		x = conveyor.connection._AbstractSocketConnection(fakeSock2, 'address')

		with self.assertRaises(conveyor.connection.ConnectionWriteException):
			x.write('data')

	# TODO : Someday in the future, we need to expand this to test recovery
	# from some IOErrors (followed by valid data) situations if we run into bugs
	def test_read(self):
		aObj = conveyor.connection.Connection()
		
		with self.assertRaises(NotImplementedError):
			data = aObj.read()


class Test_PosixSocketConnection(unittest.TestCase):
	
	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_constructor(self):
		fakeSock = mock.Mock(socket.socket)		
		if 'nt' != os.name: 
			x = conveyor.connection._PosixSocketConnection(fakeSock,'address')
		else:
			with self.assertRaises(AttributeError): # does not exist on this OS
				x = conveyor.connection._PosixSocketConnection(fakeSock,'address')
#		x = conveyor.connection._AbstractSocketConnection(fakeSock,'address')
#		x.write('data')


class Test_Win32PipedConnection(unittest.TestCase):
	
	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_constructor(self):
		fakeSock = mock.Mock(socket.socket)		
		if 'nt' != os.name: 
			with self.assertRaises(AttributeError): # does not exist on this OS
				x = conveyor.connection._Win32PipedConnection(fakeSock,'address')
		else:
			x = conveyor.connection._Win32PipedConnection(fakeSock,'address')

if __name__ == "__main__":
    unittest.main()


