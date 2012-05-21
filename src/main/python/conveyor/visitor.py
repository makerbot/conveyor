# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/visitor.py
#
# conveyor - Printing dispatch engine for 3D objects and their friends.
# Copyright © 2012 Matthew W. Samsonoff <matthew.samsonoff@makerbot.com>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, print_function, unicode_literals)

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.event

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
