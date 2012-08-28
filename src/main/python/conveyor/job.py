# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/job.py
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

class Job(object):
    def __init__(
        self, id, build_name, path, config, preprocessor, skip_start_end,
        with_start_end):
            self.build_name = build_name
            self.config = config
            self.id = id
            self.path = path
            self.preprocessor = preprocessor
            self.process = None
            self.skip_start_end = skip_start_end
            self.with_start_end = with_start_end

    def todict(self):
        dct = {
            'id': self.id,
            'build_name': self.build_name,
            'config': self.config,
            'path': self.path,
            'preprocessor': self.preprocessor,
            'skip_start_end': self.skip_start_end,
            'with_start_end': self.with_start_end
        }
        return dct
