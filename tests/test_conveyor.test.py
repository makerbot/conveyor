import sys
sys.path.insert(0,'src/main/python') # for testing only

from conveyor.test import *

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class ListHandlerTestCase(unittest.TestCase):
    def setUp(self):
        listlogging('INFO')

    def test_emit(self):
        '''Test that the ListHandler collects log messages into its list.'''
        ListHandler.list = []
        log = logging.getLogger('ListHandlerTestCase')
        log.info('info')
        self.assertEqual(1, len(ListHandler.list))
        self.assertEqual('info', ListHandler.list[0].msg)


if __name__ == '__main__':
    unittest.main()
