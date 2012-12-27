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
        cppenv.Moc4('include/conveyor/slicers.h'),
        cppenv.Moc4('include/conveyor/eeprommap.h')
    ])

tests = {}
testenv = cppenv.Clone()

if "darwin" == sys.platform:
    utilenv.Program('bin/start_conveyor_service',
                    'src/util/cpp/mac_start_conveyor_service.c')
    utilenv.Program('bin/stop_conveyor_service',
                    'src/util/cpp/mac_stop_conveyor_service.c')


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

def rInstall(dest, src, pattern='*'):
    installs = []

    print "rInstall " + src + "->" + dest

    for curpath, dirnames, filenames in os.walk(src):
        relative = os.path.relpath(curpath, src)

        print "Installing " + curpath + " into " + os.path.join(dest, relative)

        installs.append(cppenv.Install(os.path.join(dest, relative),
                                       filter(lambda f:
                                                  (os.path.exists(str(f)) and
                                                   not os.path.isdir(str(f))),
                                         Glob(os.path.join(curpath, pattern)))))

    return installs


install_prefix = ARGUMENTS.get('install_prefix', '')
config_prefix = ARGUMENTS.get('config_prefix', '')

install_bins = ['#/submodule/conveyor_bins/python']

inst = []
if sys.platform == "linux2":
    if install_prefix == '': install_prefix = '/usr'
    if config_prefix == '': config_prefix = '/etc'

    conveyor_dir = install_prefix + '/share/conveyor'
    pylib_dir = conveyor_dir + '/lib'
    mg_config_dir = install_prefix + '/share/miracle-grue'
    sk_config_dir = install_prefix + '/share/skeinforge'
    conveyor_bins_dir = conveyor_dir + '/conveyor_bins'

    inst.append(cppenv.InstallAs(config_prefix + '/conveyor.conf',
                                 'conveyor-debian.conf'))
    inst.append(cppenv.InstallAs(config_prefix + '/init/conveyor.conf',
                               'linux/conveyor-upstart.conf'))
    inst.append(cppenv.Install(install_prefix + '/lib', libconveyor))
    inst.append(cppenv.Install(conveyor_dir, 'wrapper/conveyord'))
    inst.append(cppenv.Install(conveyor_dir, 'setup.sh'))

    inst += rInstall(install_prefix + '/include/makerbot',
                     str(Dir('#/include')), '*.h')

elif sys.platform == 'darwin':
    framework_dir = install_prefix + '/Library/Frameworks/MakerBot.framework/Makerbot'
    conveyor_dir = framework_dir + '/conveyor'
    launchd_dir = '/Library/LaunchDaemons'

    if config_prefix == '': config_prefix = conveyor_dir
    pylib_dir = conveyor_dir + '/src/main/python'
    mg_config_dir = conveyor_dir + '/src/main/miraclegrue'
    sk_config_dir = conveyor_dir + '/src/main/skeinforge'
    conveyor_bins_dir = conveyor_dir + '/submodule/conveyor_bins'
    install_bins.append('#/submodule/conveyor_bins/mac')

    inst.append(cppenv.InstallAs(config_prefix + '/conveyor.conf',
                                 'conveyor-mac.conf'))
    inst.append(cppenv.Install(launchd_dir, 'mac/com.makerbot.conveyor.plist'))
    inst.append(cppenv.Install(conveyor_dir, 'setup.sh'))

elif sys.platform == 'win32':
    if install_prefix == '':
        if os.path.exists('c:/Program Files (x86)'):
            install_prefix = 'c:/Program Files (x86)/MakerBot'
        else:
            install_prefix = 'c:/Program Files/MakerBot'

    conveyor_dir = install_prefix + '/conveyor'

    if config_prefix == '': config_prefix = conveyor_dir

    pylib_dir = conveyor_dir + '/src/main/python'
    mg_config_dir = conveyor_dir + '/src/main/miraclegrue'
    sk_config_dir = conveyor_dir + '/src/main/skeinforge'
    conveyor_bins_dir = conveyor_dir + '/submodule/conveyor_bins'
    install_bins.append('#/submodule/conveyor_bins/windows')

    inst.append(cppenv.InstallAs(config_prefix + '/conveyor.conf',
                                 'conveyor-mac.conf'))
    inst.append(cppenv.Install(conveyor_dir, 'setup.bat'))
    inst.append(cppenv.Install(conveyor_dir, 'start.bat'))
    inst.append(cppenv.Install(conveyor_dir, 'stop.bat'))

    
inst += rInstall(pylib_dir, str(Dir('#/src/main/python')), '*.py')
inst += rInstall(mg_config_dir, str(Dir('#/src/main/miraclegrue')))
inst += rInstall(sk_config_dir, str(Dir('#/src/main/skeinforge')))

inst.append(cppenv.Install(conveyor_dir, 'conveyor_service.py'))
inst.append(cppenv.Install(conveyor_dir, 'conveyor_cmdline_client.py'))
inst.append(cppenv.Install(conveyor_dir, 'COPYING'))
inst.append(cppenv.Install(conveyor_dir, 'README.md'))
inst.append(cppenv.Install(conveyor_dir, 'HACKING.md'))

for conveyor_bin in install_bins:
    inst.append(rInstall(conveyor_bins_dir, str(Dir(conveyor_bin))))

env.Alias('install',inst)
