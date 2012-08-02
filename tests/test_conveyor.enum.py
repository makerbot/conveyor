from __future__ import (absolute_import, print_function, unicode_literals)

import sys
sys.path.insert(0,'src/main/python') # for testing only

import conveyor.enum as enum

try:
    import unittest2 as unittest
except ImportError:
    import unittest

class _EnumTestCase(unittest.TestCase):
    def test(self):
        '''Test the enum() function.'''

        cls = enum.enum('Test', 'A', 'B', C='c', D='d')
        self.assertEqual('A', cls.A)
        self.assertEqual('B', cls.B)
        self.assertEqual('c', cls.C)
        self.assertEqual('d', cls.D)


if __name__ == '__main__':
    unittest.main()


