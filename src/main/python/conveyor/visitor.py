# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import conveyor.event
try:
    import unittest2 as unittest
except ImportError:
    import unittest

class NoAcceptorException(ValueError):
    def __init__(self, target):
        ValueError.__init__(self, target)
        self.target = target

class Visitor(object):
    def visit(self, target, *args, **kwargs):
        for cls in  target.__class__.__mro__:
            name = ''.join(['accept_', cls.__name__])
            method = getattr(self, name, None)
            if None != method:
                result = method(target, *args, **kwargs)
                return result
        raise NoAcceptorException(target)

class _A(object):
    pass
class _B(_A):
    pass
class _C(_A):
    pass
class _D(_B, _C):
    pass

class _VisitorTestCase(unittest.TestCase):
    def setUp(self):
        self._a = _A()
        self._b = _B()
        self._c = _C()
        self._d = _D()

    def test_visit(self):
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
        v = Visitor()
        for x in (self._a, self._b, self._c, self._d):
            with self.assertRaises(NoAcceptorException):
                v.visit(x) # pragma: no cover

    def test_mro(self):
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
