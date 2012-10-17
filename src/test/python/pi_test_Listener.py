import unittest

import sys
import os

#override sys.path for testing only 
sys.path.insert(0,'./src/main/python')
import conveyor
import conveyor.listener

import socket
import mock
class TestListener(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_base_unimplemented(self):
		aObj = conveyor.listener.Listener()
		
		# as template, these should throw 'NotImplemented'
		with self.assertRaises(NotImplementedError):
			aObj.accept()

		with self.assertRaises(NotImplementedError):
			aObj.cleanup()

		with self.assertRaises(NotImplementedError): 
			# TRICKY: throwns a NotImplementedError ONLY 
			# because base cleanup is not implemented. 
			with aObj:
				pass

class Test_AbstractSocketListener(unittest.TestCase):

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_construction(self):
		with self.assertRaises(TypeError):
			x = conveyor.listener._AbstractSocketListener() # requires params
		#with raisesException(TypeError):
		x = conveyor.listener._AbstractSocketListener('8070') 
		self.assertIsInstance(x, conveyor.listener._AbstractSocketListener)		
	
	def tests_functions_defaults(self):	
		def ret_socket_addr():
			return 'socket', 'addr'
		fakeSock = mock.Mock(socket.socket)
		fakeSock.accept = ret_socket_addr
		x = conveyor.listener._AbstractSocketListener(fakeSock) 
		x.accept()

	def tests_functions_defaults(self):	
		def ret_socket_addr(*args, **kwargs):
			return 'socket', 'addr' 
		fakeSock = mock.Mock(socket.socket)
		fakeSock.accept = ret_socket_addr
		x = conveyor.listener._AbstractSocketListener(fakeSock) 
		conn = 	x.accept()
		self.assertIsInstance(conn, conveyor.connection.SocketConnection)

	# TODO: If we run into timeout bugs, we should throw some timeout and 
	# IOError types, and then verify we recover from them

	
if __name__ == "__main__":
    unittest.main()


