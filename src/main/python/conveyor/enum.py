# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/enum.py
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

def enum(name, *args, **kwargs):
    iterable = ((v, v) for v in args)
    dct = dict(iterable, **kwargs)
    # NOTE: the enumeration type's name must be a non-unicode string.
    cls = type(str(name), (), dct)
    return cls

class _EnumTestCase(unittest.TestCase):
    def test(self):
        '''Test the enum() function.'''

        cls = enum('Test', 'A', 'B', C='c', D='d')
        self.assertEqual('A', cls.A)
        self.assertEqual('B', cls.B)
        self.assertEqual('c', cls.C)
        self.assertEqual('d', cls.D)
