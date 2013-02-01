# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/doc/template.py
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

import os.path

from distutils.core import setup


setup(
    name='conveyor',
    version='2.0.0',
    author='Matthew W. Samsonoff',
    author_email='matthew.samsonoff@makerbot.com',
    url='http://github.com/makerbot/conveyor/',
    description='Printing dispatch engine for 3D objects and their friends.',
    package_dir={'': 'src/main/python'},
    packages=[
        'conveyor',
        'conveyor.client',
        'conveyor.slicer',
        'conveyor.platform',
        'conveyor.machine',
        'conveyor.machine.port',
        'conveyor.server',
    ],
)
