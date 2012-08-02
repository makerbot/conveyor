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


