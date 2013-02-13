# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/platform/linux.py
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


DEFAULT_CONFIG_FILE = '/etc/conveyor.conf'


DEFAULT_CONFIG_COMMON_ADDRESS = 'pipe:/var/run/conveyor/conveyord.socket'


DEFAULT_CONFIG_COMMON_PID_FILE = '/var/run/conveyor/conveyord.pid'


DEFAULT_CONFIG_MAKERBOT_DRIVER_AVRDUDE_EXE = '/usr/bin/avrdude'


DEFAULT_CONFIG_MAKERBOT_DRIVER_AVRDUDE_CONF_FILE = '/etc/avrdude.conf'


DEFAULT_CONFIG_MAKERBOT_DRIVER_PROFILE_DIR = '/usr/share/makerbot/s3g/profiles/'


DEFAULT_CONFIG_MIRACLE_GRUE_EXE = '/usr/bin/miracle_grue'


DEFAULT_CONFIG_MIRACLE_GRUE_PROFILE_DIR = '/usr/share/makerbot/miraclegrue/'


DEFAULT_CONFIG_SKEINFORGE_FILE = '/usr/share/makerbot/skeinforge/skeinforge_application/skeinforge.py'


DEFAULT_CONFIG_SKEINFORGE_PROFILE_DIR = '/usr/share/makerbot/skeinforge/'


DEFAULT_CONFIG_SERVER_LOGGING_FILE = '/var/log/conveyor/conveyord.log'


DEFAULT_CONFIG_SERVER_UNIFIED_MESH_HACK_EXE = '/usr/bin/unified_mesh_hack'
