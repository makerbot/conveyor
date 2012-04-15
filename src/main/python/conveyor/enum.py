# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

try:
    import unittest2 as unittest
except ImportError:
    import unittest

def enum(name, *args, **kwargs):
    iterable = ((v, v) for v in args)
    dct = dict(iterable, **kwargs)
    # NOTE: the enumeration type's name must be a non-unicode string.
    cls = type(str(name), (), dct)
    return cls

class _EnumTestCase(unittest.TestCase):
    def test(self):
        cls = enum('Test', 'A', 'B', C='c', D='d')
        self.assertEqual('A', cls.A)
        self.assertEqual('B', cls.B)
        self.assertEqual('c', cls.C)
        self.assertEqual('d', cls.D)
