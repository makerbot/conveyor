# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/decorator.py
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


def args(*funcs):
    def decorator(cls):
        # NOTE: decorators are applied bottom-up. To support positional
        # arguments (listed in the source file in a sensible manner) we have to
        # prepend the new argument functions to the list instead of appending
        # them.
        args_funcs = list(funcs) + getattr(cls, '_args_funcs', [])
        setattr(cls, '_args_funcs', args_funcs)
        return cls
    return decorator


def command(command_class):
    def decorator(cls):
        command_classes = [command_class] + getattr(cls, '_command_classes', [])
        setattr(cls, '_command_classes', command_classes)
        return cls
    return decorator


def jsonrpc(name=None):
    def decorator(func):
        setattr(func, '_jsonrpc', True)
        setattr(func, '_jsonrpc_name', name)
        return func
    return decorator
