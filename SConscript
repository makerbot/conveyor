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
from glob import glob

# We require Qt 4.8.0; Oneiric ships with 4.7.4. On Oneiric, use the manually installed SDK.
if sys.platform == 'linux2':
    import subprocess
    distro=subprocess.Popen(['lsb_release','-c','-s'], stdout=subprocess.PIPE).communicate()[0].strip()
    if distro == 'oneiric':
        os.environ['QTDIR']='/opt/QtSDK/Desktop/Qt/4.8.0/gcc/'
        os.environ['PKG_CONFIG_PATH']='/opt/QtSDK/Desktop/Qt/4.8.0/gcc/lib/pkgconfig'
    elif distro == 'precise':
        pass
    else:
        print("*** WARNING: potentially unsupported distribution! ***")

env = Environment(ENV=os.environ, tools=['default','qt4'])

utilenv = env.Clone()

Import('build_unit_tests', 'run_unit_tests')

if 'win32' == sys.platform:
    env.Tool('mb_mingw', toolpath=[Dir('submodule/mw-scons-tools')])
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
        env['QTDIR'] = os.path.expanduser('~/QtSDK/Desktop/Qt/4.8.0/gcc/')

env.Tool('qt4', toolpath=[Dir('submodule/mw-scons-tools')])
env.EnableQt4Modules(['QtCore', 'QtTest'])
env.Append(CCFLAGS='-g')
env.Append(CCFLAGS='-pedantic')
env.Append(CCFLAGS='-Wall')
env.Append(CCFLAGS='-Wextra')
env.Append(CCFLAGS='-Wno-variadic-macros')
env.Append(CCFLAGS='-Wno-long-long')
env.Append(CCFLAGS='-Werror') # I <3 -Werror. It is my favorite -W flag.

cppenv = env.Clone()
cppenv.Append(CPPPATH=Dir('#/include/'))

cppenv.Tool('mb_install', toolpath=[Dir('submodule/mw-scons-tools')])
env.Tool('mb_install', toolpath=[Dir('submodule/mw-scons-tools')])

cppenv.MBAddDevelLibPath('#/../jsonrpc/obj')
cppenv.MBAddDevelLibPath('#/../json-cpp/obj')
cppenv.MBAddDevelIncludePath('#/../jsonrpc/src/main/include')
cppenv.MBAddDevelIncludePath('#/../json-cpp/include')

cppenv.MBAddLib('jsoncpp')
cppenv.MBAddLib('jsonrpc')

if sys.platform == 'win32':
    cppenv.Append(LIBS=['ws2_32'])


libconveyor_cpp = [Glob('src/main/cpp/*.cpp')]
if 'win32' != sys.platform:
    libconveyor_cpp.append(Glob('src/main/cpp/posix/*.cpp'))
else:
    libconveyor_cpp.append(Glob('src/main/cpp/win32/*.cpp'))

cppenv.MBSetLibSymName('conveyor')
libconveyor = cppenv.SharedLibrary(
    'conveyor', [
        libconveyor_cpp,
        cppenv.Moc4('include/conveyor/conveyor.h'),
        cppenv.Moc4('include/conveyor/job.h'),
        cppenv.Moc4('include/conveyor/printer.h'),
        cppenv.Moc4('include/conveyor/slicers.h'),
        cppenv.Moc4('include/conveyor/eeprommap.h')
    ])

cppenv.MBInstallLib(libconveyor, 'conveyor')
cppenv.MBInstallHeaders(env.MBGlob('#/include/conveyor/*'), 'conveyor')
env.Clean(libconveyor, '#/obj')

tests = {}
testenv = cppenv.Clone()

utilenv.Tool('mb_install', toolpath=[Dir('submodule/mw-scons-tools')])
if "darwin" == sys.platform:
    startcmd = utilenv.Program('bin/start_conveyor_service',
                               'src/util/cpp/mac_start_conveyor_service.c')
    stopcmd = utilenv.Program('bin/stop_conveyor_service',
                              'src/util/cpp/mac_stop_conveyor_service.c')

    utilenv.MBInstallBin(startcmd)
    utilenv.MBInstallBin(stopcmd)


if build_unit_tests:
    testenv.Append(LIBS='cppunit')

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

conveyor_pysrc = []
for curpath, dirnames, filenames in os.walk(str(Dir('#/src/main/python'))):
    conveyor_pysrc.append(filter(lambda f:
                                 (os.path.exists(str(f)) and
                                  not os.path.isdir(str(f))),
                             env.Glob(os.path.join(curpath, '*.py'))))

                             
setup_script = 'setup_conveyor_env.py'
paths = [os.path.join('submodule', 'conveyor_bins', 'python')]

if env.MBUseDevelLibs():
    paths.append(os.path.join('..', 'pyserial', 'dist'))
    paths.append(os.path.join('..', 's3g', 'dist'))
else:
    if env.MBIsLinux() and 'MB_SYSTEM_EGG_DIR' in env:
        paths.append(env['MB_SYSTEM_EGG_DIR'])
    else:
        paths.append(env['MB_EGG_DIR'])
    
# add quoting. 
paths = ['"'+path+'"' for path in paths]
    
vcmd = env.Command('#/virtualenv', setup_script,
                   ' '.join(['python', os.path.join('.', setup_script)] + paths))

                   
if env.MBIsWindows():
    pycmd = 'virtualenv\\Scripts\\python'
else:
    pycmd = 'virtualenv/bin/python'

conveyor_egg = env.Command('#/dist/conveyor-2.0.0-py2.7.egg',
                      conveyor_pysrc + [vcmd],
                      pycmd + ' -c "import setuptools; execfile(\'setup.py\')" bdist_egg')

env.MBInstallEgg(conveyor_egg)
env.Clean(vcmd,'#/virtualenv')

if env.MBIsMac():
    py26cmd = 'virtualenv26/bin/python'
    vcmd26 = env.Command('#/virtualenv26', setup_script,
                         ' '.join(['python2.6', os.path.join('.', setup_script)] + paths))

    conveyor_egg26 = env.Command('#/dist/conveyor-2.0.0-py2.6.egg',
                                 conveyor_pysrc + [vcmd26],
                                 py26cmd + ' -c "import setuptools; execfile(\'setup.py\')" bdist_egg')
    env.MBInstallEgg(conveyor_egg26)
    env.Clean(vcmd26,'#/virtualenv26')




env.Clean(conveyor_egg, '#/build')
env.Clean(conveyor_egg, '#/src/main/python/conveyor.egg-info')

if sys.platform == "linux2":
    #env.MBInstallConfig(env.MBGlob('#/linux/*'))
    #env.MBInstallBin('#/wrapper/conveyord')
    env.MBInstallConfig('#/conveyor-debian.conf', 'conveyor.conf')
    env.MBInstallConfig('#/data/conveyor.conf', 'init/conveyor.conf')

elif sys.platform == 'darwin':
    launchd_dir = 'Library/LaunchDaemons'

    env.MBInstallResources(env.MBGlob('#/submodule/conveyor_bins/mac/*'))
    env.MBInstallResources(env.MBGlob('#/mac/*'))
    env.MBInstallConfig('#/conveyor-mac.conf', 'conveyor.conf')
    env.MBInstallSystem('#/mac/com.makerbot.conveyor.plist',
                        os.path.join(launchd_dir,
                                     'com.makerbot.conveyor.plist'))

elif sys.platform == 'win32':
    env.MBInstallResources(env.MBGlob('#/submodule/conveyor_bins/windows/*'))
    env.MBInstallResources(env.MBGlob('#/win/*'))
    env.MBInstallConfig('#/conveyor-win32.conf', 'conveyor.conf')

    env.MBInstallBin('#/restart.bat')
    env.MBInstallBin('#/start.bat')
    env.MBInstallBin('#/stop.bat')

env.MBInstallEgg(env.MBGlob('#/submodule/conveyor_bins/python/*'))
    
env.MBInstallResources('#/src/main/miraclegrue')
env.MBInstallResources('#/src/main/skeinforge/Replicator slicing defaults', 'skeinforge')

env.MBInstallResources('#/conveyor_service.py')
env.MBInstallResources('#/conveyor_cmdline_client.py')
env.MBInstallResources('#/virtualenv.py')
env.MBInstallResources('#/setup_conveyor_env.py')

env.MBInstallResources('#/src/test/stl/single.stl', 'testfiles')
env.MBInstallResources('#/src/test/stl/left.stl', 'testfiles')
env.MBInstallResources('#/src/test/gcode/single.gcode', 'testfiles')

env.MBCreateInstallTarget()
cppenv.MBCreateInstallTarget()
utilenv.MBCreateInstallTarget()

#env.Clean('#/virtualenv')
#env.Clean('#/virtualenv.pyc')
