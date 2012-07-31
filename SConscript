# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:syntax=python:ts=4:
# conveyor/SConscript
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

import os.path
import sys
import fnmatch

env = Environment(ENV=os.environ, tools=['default','qt4'])

if 'win32' == sys.platform:
    env.Tool('mingw')
    env.Replace(CCFLAGS=[])

if 'QTDIR' not in env:
    moc = env.WhereIs('moc-qt4') or env.WhereIs('moc4') or env.WhereIs('moc')
    if moc:
        env['QTDIR'] = os.path.dirname(os.path.dirname(moc))

env.EnableQt4Modules(['QtCore', 'QtTest'])
env.Append(CCFLAGS='-g')
env.Append(CCFLAGS='-pedantic')
env.Append(CCFLAGS='-Wall')
env.Append(CCFLAGS='-Wextra')
env.Append(CCFLAGS='-Wno-variadic-macros')
env.Append(CCFLAGS='-Wno-long-long')
env.Append(CCFLAGS='-Werror') # I <3 -Werror. It is my favorite -W flag.

cppenv = env.Clone()
cppenv.Append(CPPPATH=Dir('src/main/cpp/conveyor'))
cppenv.Append(CPPPATH=Dir('include'))
libconveyor = cppenv.Library('conveyor', Glob('src/main/cpp/conveyor/*.cpp'))

inst = []
inst.append(cppenv.InstallAs( 'etc/conveyor.conf','conveyor-debian.conf'))
inst.append(cppenv.Install('usr/lib',libconveyor))
inst.append(cppenv.Install('usr/include','include/conveyor.h'))

pysrc_root = str(Dir('#/src/main/python'))
for root,dirnames,filenames in os.walk(pysrc_root):
    for filename in fnmatch.filter(filenames,'*.py'):
    	rpath = os.path.relpath(root,pysrc_root)
    	outdir = os.path.join('module',rpath)
    	insrc = os.path.join(root,filename)
    	inst.append(cppenv.Install(outdir,insrc))
    	print outdir,insrc

env.Alias('install',inst)

'''
testenv = cppenv.Clone()
testenv.AlwaysBuild('check')
testenv.Append(LIBS=libjsonrpc)
for node in Glob('#/obj/src/test/cpp/test-*.cpp'):
    root, ext = os.path.splitext(os.path.basename(node.abspath))
    test = testenv.Program(root, [node])
    alias = testenv.Alias('check', [test], test[0].abspath)
    testenv.AlwaysBuild(alias)
'''
