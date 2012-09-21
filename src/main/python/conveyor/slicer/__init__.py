# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/slicer/__init__.py
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

import logging

class Slicer(object):
    def __init__(self, configuration):
        self._configuration = configuration
        self._log = logging.getLogger(self.__class__.__name__)

    def _update_progress(self, current_progress, new_progress, task):
        if None is not new_progress and new_progress != current_progress:
            current_progress = new_progress
            task.heartbeat(current_progress)
        return current_progress

    def slice(
        self, profile, inputpath, outputpath, with_start_end,
        slicer_settings, material, task):
            raise NotImplementedError
