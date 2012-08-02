#!/usr/bin/python
try:
    import unittest2 as unittest
except ImportError:
    import unittest
import logging


#Configure logging (This should only be done for testing, nowhere else)
logging.basicConfig()
#Disable logging
logging.disable(100)

if __name__ == "__main__":
  all_tests = unittest.TestLoader().discover('tests', pattern='*.py')
  unittest.TextTestRunner().run(all_tests)


