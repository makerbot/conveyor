# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/platform/windows.py
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

import os.path


_PROGRAM_FILES_X86_DIR = os.path.join('C:\\', 'Program Files (x86)')


if os.path.exists(_PROGRAM_FILES_X86_DIR):
    PROGRAM_FILES_DIR = _PROGRAM_FILES_X86_DIR
else:
    PROGRAM_FILES_DIR = os.path.join('C:\\', 'Program Files')


DEFAULT_CONFIG_FILE = 'conveyor.conf'


DEFAULT_CONFIG_COMMON_ADDRESS = 'tcp:127.0.0.1:9999'


DEFAULT_CONFIG_COMMON_PID_FILE = 'conveyord.pid'


DEFAULT_CONFIG_MAKERBOT_DRIVER_AVRDUDE_EXE = 'avrdude.exe'


DEFAULT_CONFIG_MAKERBOT_DRIVER_AVRDUDE_CONF_FILE = 'avrdude.conf'


DEFAULT_CONFIG_MAKERBOT_DRIVER_PROFILE_DIR = os.path.join('s3g', 'profiles')


DEFAULT_CONFIG_MIRACLE_GRUE_EXE = 'miracle_grue.exe'


DEFAULT_CONFIG_MIRACLE_GRUE_PROFILE_DIR = 'miraclegrue'


DEFAULT_CONFIG_SKEINFORGE_FILE = os.path.join('skeinforge', 'skeinforge_application', 'skeinforge.py')


DEFAULT_CONFIG_SKEINFORGE_PROFILE_DIR = 'skeinforge'


DEFAULT_CONFIG_SERVER_LOGGING_FILE = 'conveyord.log'


DEFAULT_CONFIG_SERVER_UNIFIED_MESH_HACK_EXE = 'unified_mesh_hack.exe'
