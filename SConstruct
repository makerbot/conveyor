# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:syntax=python:ts=4:
# conveyor/SConstruct
#
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

import sys, os
AddOption('--test', action='store_true', dest='test')
run_test = GetOption('test')


env = Environment(ENV=os.environ)

if 'win32' == sys.platform:
   	env.Command('virtualenv', 'setup.bat', 'setup.bat')
else:
	env.Command('virtualenv', 'setup.sh', './setup.sh')

if run_test:
    if 'win32' == sys.platform:
        env.Command('test', 'test.bat', 'test.bat')
    else: 
        env.Command('test', 'test.sh', '. virtualenv/bin/activate; ./test.sh')

## For building C++/Qt creation
SConscript('SConscript', variant_dir='obj', duplicate=1)
