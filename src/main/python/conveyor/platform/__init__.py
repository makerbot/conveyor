# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/platform/__init__.py
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

import sys

import conveyor.enum
import conveyor.error


Platform = conveyor.enum.enum('Platform', 'LINUX', 'OSX', 'WINDOWS')


if sys.platform.startswith('linux'):
    PLATFORM = Platform.LINUX
elif sys.platform.startswith('darwin'):
    PLATFORM = Platform.OSX
elif sys.platform.startswith('win'):
    PLATFORM = Platform.WINDOWS
else:
    raise ValueError(sys.platform)


def is_linux():
    result = Platform.LINUX == PLATFORM
    return result


def is_osx():
    result = Platform.OSX == PLATFORM
    return result


def is_windows():
    result = Platform.WINDOWS == PLATFORM
    return result


def is_posix():
    result = is_linux() or is_osx()
    return result


if is_posix():
    from conveyor.platform.posix import *

if is_linux():
    from conveyor.platform.linux import *
elif is_osx():
    from conveyor.platform.osx import *
elif is_windows():
    from conveyor.platform.windows import *
else:
    raise conveyor.error.UnsupportedPlatformException(sys.platform)
