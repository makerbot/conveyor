import sys
sys.path.insert(0,'src/main/python') # for testing only

import conveyor.cient

try:
    import unittest2 as unittest
except ImportError:
    import unittest

class ClientMainTestCase(unittest.TestCase):
   
  def setUp(self):
    pass

  def tearDown(self):
    pass
  
  def test_client_anything(self):
    self.assertEqual(True, False, "Test something Dammit")
    
if __name__ == '__main__':
    unittest.main()

