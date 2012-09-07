# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:syntax=python:ts=4:
# conveyor/SConscript
#
# Copyright © 2012 Matthew W. Samsonoff <matthew.samsonoff@makerbot.com>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.

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
import re
import glob

# We require Qt 4.8.1; Oneiric ships with 4.7.4. On Oneiric, use the manually installed SDK.
if sys.platform == 'linux2':
    import subprocess
    distro=subprocess.Popen(['lsb_release','-c','-s'], stdout=subprocess.PIPE).communicate()[0].strip()
    if distro == 'oneiric':
        os.environ['QTDIR']='/opt/QtSDK/Desktop/Qt/4.8.1/gcc/'
        os.environ['PKG_CONFIG_PATH']='/opt/QtSDK/Desktop/Qt/4.8.1/gcc/lib/pkgconfig'
    elif distro == 'precise':
        pass
    else:
        print("*** WARNING: potentially unsupported distribution! ***")

env = Environment(ENV=os.environ, tools=['default','qt4'])

Import('build_unit_tests', 'run_unit_tests')

if 'win32' == sys.platform:
    env.Tool('mingw')
    env.Replace(CCFLAGS=[])

#NOTE: If you put '~'s in your bash profile, youre gonna have
#a bad time.  Scons cant expand them correctly, so it won't be 
#able to find your moc.  In your path, put the entire path (from '/')
#PS: Make sure you have QT's pkg_config path defined as an environemnt
#variable as $PKG_CONFIG_PATH
if 'QTDIR' not in env:
    moc = env.WhereIs('moc-qt4') or env.WhereIs('moc4') or env.WhereIs('moc')
    if moc:
        env['QTDIR'] = os.path.dirname(os.path.dirname(moc))
    elif 'darwin' == sys.platform:
        env['QTDIR'] = os.path.expanduser('~/QtSDK/Desktop/Qt/4.8.1/gcc/')

env.Tool('qt4', toolpath=[Dir('src/main/scons/')])
env.EnableQt4Modules(['QtCore', 'QtTest'])
env.Append(CCFLAGS='-g')
env.Append(CCFLAGS='-pedantic')
env.Append(CCFLAGS='-Wall')
env.Append(CCFLAGS='-Wextra')
env.Append(CCFLAGS='-Wno-variadic-macros')
env.Append(CCFLAGS='-Wno-long-long')
env.Append(CCFLAGS='-Werror') # I <3 -Werror. It is my favorite -W flag.

cppenv = env.Clone()
cppenv.Append(CPPPATH=Dir('include/'))
if ARGUMENTS.get('debian_build',0):
    cppenv.Append(CPPPATH=Dir('/usr/include/makerbot/'))
else:
    cppenv.Append(CPPPATH=Dir('#/../jsonrpc/src/main/include/'))
    cppenv.Append(CPPPATH=Dir('#/../json-cpp/include/'))
libconveyor_cpp = [Glob('src/main/cpp/*.cpp')]
if 'win32' != sys.platform:
    libconveyor_cpp.append(Glob('src/main/cpp/posix/*.cpp'))
else:
    libconveyor_cpp.append(Glob('src/main/cpp/win32/*.cpp'))
libconveyor = cppenv.StaticLibrary(
    'conveyor', [
        libconveyor_cpp,
        cppenv.Moc4('include/conveyor/conveyor.h'),
        cppenv.Moc4('include/conveyor/job.h'),
        cppenv.Moc4('include/conveyor/printer.h'),
        cppenv.Moc4('include/conveyor/slicers.h')
    ])

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
        # print outdir,insrc

env.Alias('install',inst)


tests = {}
testenv = cppenv.Clone()

if build_unit_tests:
    testenv.Append(LIBS='cppunit')

    if ARGUMENTS.get('debian_build',0):
        testenv.Append(LIBPATH=[Dir('/usr/lib/makerbot')])
    	testenv.Append(LIBS=['jsonrpc'])
    	testenv.Append(LIBS=['json'])
    else:
        testenv.Append(LIBPATH=[Dir('#/../json-cpp/obj/')])
    	testenv.Append(LIBPATH=[Dir('#/../jsonrpc/obj/')])
    	testenv.Append(LIBS=['jsonrpc'])
    	testenv.Append(LIBS=['json'])

    if 'win32' == sys.platform:
        testenv.Append(LIBS=['ws2_32'])

    test_common = ['src/test/cpp/UnitTestMain.cpp', libconveyor]

    testre = re.compile('(([^/]+)TestCase\.cpp)$')
    for testsrc in Glob('src/test/cpp/*'):
        match = testre.search(str(testsrc))

        if match is not None:
            testfile = match.group(1)
            testname = match.group(2)

            test = testenv.Program('bin/unit_tests/{}UnitTest'.format(testname),
                                   [testsrc] + test_common)

            tests[testname] = test

if run_unit_tests:
    for (name, test) in tests.items():
        testenv.Command('runtest_test_'+name, test, test)


