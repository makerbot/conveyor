from __future__ import (absolute_import, print_function, unicode_literals)

import sys
sys.path.insert(0,'src/main/python') # for testing only

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from conveyor.visitor import *

class _A(object):
    pass
class _B(_A):
    pass
class _C(_A):
    pass
class _D(_B, _C):
    pass


class VisitorTestCase(unittest.TestCase):
    def setUp(self):
        self._a = _A()
        self._b = _B()
        self._c = _C()
        self._d = _D()

    def test_visit(self):
        '''Test that the visitor works.'''

        callback = conveyor.event.Callback()
        class V(Visitor):
            def accept__A(self_v, target, *args, **kwargs):
                callback(*args, **kwargs)
                return target
        v = V()
        for x in (self._a, self._b, self._c, self._d):
            callback.reset()
            self.assertFalse(callback.delivered)
            self.assertEqual(None, callback.args)
            self.assertEqual(None, callback.kwargs)
            result = v.visit(x, 1, b=2)
            self.assertEqual(x, result)
            self.assertTrue(callback.delivered)
            self.assertEqual((1,), callback.args)
            self.assertEqual({'b': 2}, callback.kwargs)

    def test_NoAcceptorException(self):
        '''Test that the visitor throws a NoAcceptorException when there is no
        acceptor method for the value.

        '''

        v = Visitor()
        for x in (self._a, self._b, self._c, self._d):
            with self.assertRaises(NoAcceptorException):
                v.visit(x) # pragma: no cover

    def test_mro(self):
        '''Test that the visitor searches for acceptor methods based on the
        type's method resolution order.

        '''

        callback = conveyor.event.Callback()

        # MRO Reference:
        #
        #   a: _A
        #   b: _B, _A
        #   c: _C, _A
        #   d: _D, _B, _C, _A

        class V1(Visitor):
            def accept__A(self_v1, target, *args, **kwargs): # pragma: no cover
                self.fail()
            def accept__B(self_v1, target, *args, **kwargs): # pragma: no cover
                self.fail()
            def accept__C(self_v1, target, *args, **kwargs): # pragma: no cover
                self.fail()
            def accept__D(self_v1, target, *args, **kwargs):
                callback(*args, **kwargs)
                return target

        class V2(Visitor):
            def accept__A(self_v1, target, *args, **kwargs): # pragma: no cover
                self.fail()
            def accept__B(self_v1, target, *args, **kwargs):
                callback(*args, **kwargs)
                return target
            def accept__C(self_v1, target, *args, **kwargs): # pragma: no cover
                self.fail()

        class V3(Visitor):
            def accept__A(self_v1, target, *args, **kwargs): # pragma: no cover
                self.fail()
            def accept__C(self_v1, target, *args, **kwargs):
                callback(*args, **kwargs)
                return target

        class V4(Visitor):
            def accept__A(self_v1, target, *args, **kwargs):
                callback(*args, **kwargs)
                return target

        for cls in (V1, V2, V3, V4):
            v = cls()
            callback.reset()
            self.assertFalse(callback.delivered)
            self.assertEqual(None, callback.args)
            self.assertEqual(None, callback.kwargs)
            result = v.visit(self._d, 1, b=2)
            self.assertEqual(self._d, result)
            self.assertTrue(callback.delivered)
            self.assertEqual((1,), callback.args)
            self.assertEqual({'b': 2}, callback.kwargs)

if __name__ == '__main__':
    unittest.main()


