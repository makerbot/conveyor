# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/platform/osx.py
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


DEFAULT_CONFIG_FILE = '/Library/MakerBot/conveyor.conf'


DEFAULT_CONFIG_COMMON_ADDRESS = 'pipe:/var/tmp/conveyord.socket'


DEFAULT_CONFIG_COMMON_PID_FILE = '/var/tmp/conveyord.pid'


DEFAULT_CONFIG_MAKERBOT_DRIVER_AVRDUDE_EXE = '/Library/MakerBot/avrdude'


DEFAULT_CONFIG_MAKERBOT_DRIVER_AVRDUDE_CONF_FILE = '/Library/MakerBot/avrdude.conf'


DEFAULT_CONFIG_MAKERBOT_DRIVER_PROFILE_DIR = '/Library/MakerBot/s3g/profiles/'


DEFAULT_CONFIG_MIRACLE_GRUE_EXE = '/Library/MakerBot/miracle_grue'


DEFAULT_CONFIG_MIRACLE_GRUE_PROFILE_DIR = '/Library/MakerBot/miraclegrue/'


DEFAULT_CONFIG_SKEINFORGE_FILE = '/Library/MakerBot/skeinforge/skeinforge_application/skeinforge.py'


DEFAULT_CONFIG_SKEINFORGE_PROFILE_DIR = '/Library/MakerBot/skeinforge/'


DEFAULT_CONFIG_SERVER_LOGGING_FILE = '/var/log/conveyor/conveyord.log'


DEFAULT_CONFIG_SERVER_UNIFIED_MESH_HACK_EXE = '/Library/MakerBot/unified_mesh_hack'
