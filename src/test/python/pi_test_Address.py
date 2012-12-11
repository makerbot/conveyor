import unittest

import sys
import os

#override sys.path for testing only 
sys.path.insert(0,'./src/main/python')
import conveyor
import conveyor.address 

class TestAddress(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_address_factory(self):
        with self.assertRaises(conveyor.address.UnknownProtocolException):
            addr = conveyor.address.Address.address_factory("fail")
        
        # Can construct a pipe with weird/invalid name. Expected?
        addrObj1 = conveyor.address.Address.address_factory('pipe:foo-bar')
        self.assertIsInstance(addrObj1, conveyor.address._AbstractPipeAddress)

        if os.name is not 'nt' : # posix cases
            self.assertIsInstance(addrObj1, conveyor.address._PosixPipeAddress)
        else:  # windows cases
            self.assertIsInstance(addrObj1, conveyor.address._Win23PipeAddress)

        # Can't construct a tcp with weird/invalid name. Expected?
        addrObj2 = conveyor.address.Address.address_factory('tcp:something:80')
        self.assertIsInstance(addrObj2, conveyor.address.TcpAddress)

    def test_base_unimplemented(self):
        aObj = conveyor.address.Address()
        
        # as template, these should throw 'NotImplemented'
        with self.assertRaises(NotImplementedError):
            aObj.listen()

        with self.assertRaises(NotImplementedError):
            aObj.connect()


class Test_AbstractPipeAddress(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_address_factory(self):
        # Can construct a pipe with weird/invalid name. Expected?
        addrObj1 = conveyor.address._AbstractPipeAddress._factory('pipe:foo-bar',
        ['pipe','foo-bar'])
        self.assertIsInstance(addrObj1, conveyor.address._AbstractPipeAddress)

        if os.name is not 'nt' : # posix cases
            self.assertIsInstance(addrObj1, conveyor.address._PosixPipeAddress)
        else:  # windows cases
            self.assertIsInstance(addrObj1, conveyor.address._Win23PipeAddress)



class TestTcpAddress(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_address_factory(self):
        with self.assertRaises(conveyor.address.UnknownProtocolException):
            addr = conveyor.address.TcpAddress._factory('fail:sauce', ['fail','sauce'])

        with self.assertRaises(conveyor.address.MailformedUrlException):
            addr = conveyor.address.TcpAddress._factory('tcp:8080',['tcp','8080'])
            
        addrObj1 = conveyor.address.Address.address_factory('tcp:example.com:80')
        self.assertIsInstance(addrObj1, conveyor.address.TcpAddress)


    def test_get_listener(self):
    
        # test string port numbers fail 
        with self.assertRaises(TypeError):  
            y = conveyor.address.TcpAddress('localhost', '8080')
            listener = y.listen()

        # test 'foregin' host names fail 
        with self.assertRaises(Exception):  
            y = conveyor.address.TcpAddress('example.com', 8080)
            listener = y.listen()
        
        #test legit connection cretion 
        y = conveyor.address.TcpAddress('localhost', 8080)
        self.assertIsInstance(y, conveyor.address.TcpAddress)
        listener = y.listen()

        #test 2nd lister additon fails
        with self.assertRaises(Exception): # 'Error, Address already in use        
            z = conveyor.address.TcpAddress('localhost', 8080)
            self.assertIsInstance(z, conveyor.address.TcpAddress)
            listener = z.listen()



if __name__ == "__main__":
    unittest.main()

