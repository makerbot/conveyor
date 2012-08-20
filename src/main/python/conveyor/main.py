# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/main.py
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

import argparse
import decimal
import json
import logging
import os
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.debug
import conveyor.ipc

class AbstractMain(object):
    def __init__(self, program, configsection):
        self._address = None
        self._config = None
        self._configsection = configsection
        self._eventthreads = []
        self._log = logging.getLogger(self.__class__.__name__)
        self._parser = None
        self._parsedargs = None
        self._program = program
        self._socket = None
        self._unparsedargs = None

    def _sequence(self, *stages):
        code = None
        for stage in stages:
            code = stage()
            if None is not code:
                break
        return code

    def _getstages(self):
        '''Return an iterable of stages for the program to execute.'''

        yield self._initparser
        yield self._initsubparsers
        yield self._parseargs
        yield self._setrootlogger
        yield self._loadconfig
        yield self._setconfigdefaults
        yield self._checkconfig
        yield self._initlogging
        yield self._parseaddress
        yield self._run

    def _initparser(self):
        '''Initialize the command-line argument parser.'''

        self._parser = argparse.ArgumentParser(prog=self._program)
        def error(message):
            self._log.error(message)
            sys.exit(2)
        self._parser.error = error # monkey patch!
        self._initparser_common(self._parser)
        return None

    def _initparser_common(self, parser):
        parser.add_argument(
            '-c',
            '--config',
            default='/etc/conveyor/conveyor.conf',
            type=str,
            help='the configuration file',
            metavar='FILE')
        parser.add_argument(
            '-l',
            '--level',
            default=None,
            type=str,
            choices=('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG',
                'NOTSET',),
            required=False,
            help='set the log level',
            metavar='LEVEL')
        parser.add_argument(
            '-v',
            '--version',
            action='version',
            help='show the version message and exit',
            version='%(prog)s 0.1.0.0')

    def _initsubparsers(self):
        raise NotImplementedError

    def _parseargs(self):
        self._parsedargs = self._parser.parse_args(self._unparsedargs[1:])
        return None

    def _setrootlogger(self):
        if self._parsedargs.level:
            root = logging.getLogger()
            root.setLevel(self._parsedargs.level)
        return None

    def _loadconfig(self):
        try:
            with open(self._parsedargs.config, 'r') as fp:
                self._config = json.load(fp)
        except EnvironmentError as e:
            code = 1
            self._log.critical(
                'failed to open configuration file: %s: %s',
                self._parsedargs.config, e.strerror, exc_info=True)
        except ValueError:
            code = 1
            self._log.critical(
                'failed to parse configuration file: %s',
                self._parsedargs.config, exc_info=True)
        else:
            code = None
        return code

    def _setconfigdefaults(self):
        code = self._sequence(
            self._setconfigdefaults_common,
            self._setconfigdefaults_miraclegrue,
            self._setconfigdefaults_skeinforge,
            self._setconfigdefaults_server,
            self._setconfigdefaults_client)
        return code

    def _getconveyordir(self):
        conveyordir = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), '../../../../')
        return conveyordir

    # Mac OS X treats /var/run differently than other unices and
    # launchd has no reliable way to create a /var/run/conveyor on launch.
    # Ideally conveyord should create this directory itself on OS X. However
    # we're going to leave that aside for now and get it done.
    def _setconfigdefaults_common(self):
        if os.platform == 'darwin':
            defsock = 'unix:/var/run/conveyord.socket'
        else:
            defsock = 'unix:/var/run/conveyor/conveyord.socket'
        self._config.setdefault('common', {})
        self._config['common'].setdefault(
            'socket', defsock)
        self._config['common'].setdefault('slicer', 'miraclegrue')
        self._config['common'].setdefault('serialport', '/dev/ttyACM0')
        self._config['common'].setdefault('profile', 'ReplicatorSingle')
        self._config['common'].setdefault('profiledir', 'submodule/s3g/s3g/profiles')
        self._config['common'].setdefault('daemon_lockfile', 'conveyord.avail.lock')
        return None

    def _setconfigdefaults_miraclegrue(self):
        self._config.setdefault('miraclegrue', {})
        conveyordir = self._getconveyordir()
        path = os.path.abspath(
            os.path.join(
                conveyordir, 'submodule/Miracle-Grue/bin/miracle_grue'))
        self._config['miraclegrue'].setdefault('path', path)
        config = os.path.abspath(
            os.path.join(
                conveyordir, 'submodule/Miracle-Grue/miracle-pla.config'))
        self._config['miraclegrue'].setdefault('config', config)

    def _setconfigdefaults_skeinforge(self):
        self._config.setdefault('skeinforge', {})
        conveyordir = self._getconveyordir()
        path = os.path.abspath(
            os.path.join(
                conveyordir,
                'submodule/skeinforge/skeinforge_application/skeinforge.py'))
        self._config['skeinforge'].setdefault('path', path)
        profile = os.path.abspath(
            os.path.join(
                conveyordir,
                'src/main/skeinforge/Replicator slicing defaults'))
        self._config['skeinforge'].setdefault('profile', profile)

    # See above comments for why we do an explicit check for Mac OS X.
    def _setconfigdefaults_server(self):
        if os.platform == 'darwin':
            defpid = '/var/run/conveyord.pid'
        else:
            defpid = '/var/run/conveyor/conveyord.pid'
        self._config.setdefault('server', {})
        self._config['server'].setdefault(
            'pidfile', defpid)
        self._config['server'].setdefault('chdir', True)
        self._config['server'].setdefault('eventthreads', 2)
        self._config['server'].setdefault('blacklisttime', 10.0)
        self._config['server'].setdefault('logging', None)
        return None

    def _setconfigdefaults_client(self):
        self._config.setdefault('client', {})
        self._config['client'].setdefault('eventthreads', 2)
        self._config['client'].setdefault('logging', None)
        return None

    def _checkconfig(self):
        code = self._sequence(
            self._checkconfig_common,
            self._checkconfig_miraclegrue,
            self._checkconfig_skeinforge,
            self._checkconfig_server,
            self._checkconfig_client)
        return code

    def _checkconfig_common(self):
        code = self._sequence(
            self._checkconfig_common_profile,
            self._checkconfig_common_profiledir,
            self._checkconfig_common_slicer,
            self._checkconfig_common_socket,
            self._checkconfig_common_daemonfile)
        return code

    def _checkconfig_common_daemonfile(self):
        code = self._require_string('common', 'daemon_lockfile')
        return code

    def _checkconfig_common_profile(self):
        code = self._require_string('common', 'profile')
        return code

    def _checkconfig_common_profiledir(self):
        code = self._require_string('common', 'profiledir')
        return code

    def _checkconfig_common_slicer(self):
        code = self._require_string('common', 'slicer')
        if None is code:
            value = self._config['common']['slicer']
            if value not in ('miraclegrue', 'skeinforge'):
                code = 1
                self._log.critical(
                    "unsupported value for 'common/slicer': %s", value)
        return code

    def _checkconfig_common_socket(self):
        code = self._require_string('common', 'socket')
        return code

    def _checkconfig_miraclegrue(self):
        code = self._sequence(
            self._checkconfig_miraclegrue_path,
            self._checkconfig_miraclegrue_config)
        return code

    def _checkconfig_miraclegrue_path(self):
        code = self._require_string('miraclegrue', 'path')
        return code

    def _checkconfig_miraclegrue_config(self):
        code = self._require_string('miraclegrue', 'config')
        return code

    def _checkconfig_skeinforge(self):
        code = self._sequence(
            self._checkconfig_skeinforge_path,
            self._checkconfig_skeinforge_profile)
        return code

    def _checkconfig_skeinforge_path(self):
        code = self._require_string('skeinforge', 'path')
        return code

    def _checkconfig_skeinforge_profile(self):
        code = self._require_string('skeinforge', 'profile')
        return code

    def _checkconfig_server(self):
        code = self._sequence(
            self._checkconfig_server_pidfile,
            self._checkconfig_server_chdir,
            self._checkconfig_server_blacklisttime,
            self._checkconfig_server_eventthreads)
        return code

    def _checkconfig_server_pidfile(self):
        code = self._require_string('server', 'pidfile')
        return code

    def _checkconfig_server_chdir(self):
        code = self._require_bool('server', 'chdir')
        return code

    def _checkconfig_server_eventthreads(self):
        code = self._require_number('server', 'eventthreads')
        return code

    def _checkconfig_server_blacklisttime(self):
        code = self._require_number('server', 'blacklisttime')
        return code

    def _checkconfig_client(self):
        code = self._sequence(self._checkconfig_client_eventthreads)
        return code

    def _checkconfig_client_eventthreads(self):
        code = self._require_number('client', 'eventthreads')
        return code

    def _require(self, type, typename, *path):
        value = self._config
        for name in path:
            value = value[name]
        if isinstance(value, type):
            code = None
        else:
            code = 1
            self._log.critical(
                "configuration value '%s' is not a %s: %s",
                '/'.join(path), typename, value)
        return code

    def _require_bool(self, *path):
        code = self._require(bool, 'boolean', *path)
        return code

    def _require_number(self, *path):
        code = self._require((decimal.Decimal, float, int), 'number', *path)
        return code

    def _require_string(self, *path):
        code = self._require(basestring, 'string', *path)
        return code

    def _initlogging(self):
        dct = self._config[self._configsection].get('logging')
        if None is dct:
            code = None
        else:
            dct['incremental'] = False
            dct['disable_existing_loggers'] = False
            try:
                logging.config.dictConfig(dct)
            except ValueError as e:
                code = 1
                self._log.critical(
                    'invalid logging configuration: %s', e.message,
                    exc_info=True)
            else:
                code = None
                if self._parsedargs.level:
                    root = logging.getLogger()
                    root.setLevel(self._parsedargs.level)
        return code

    def _parseaddress(self):
        value = self._config['common']['socket']
        try:
            self._address = conveyor.ipc.getaddress(value)
        except conveyor.ipc.UnknownProtocolException as e:
            code = 1
            self._log.error('unknown socket protocol: %s', e.protocol)
        except conveyor.ipc.MissingHostException as e:
            code = 1
            self._log.error('missing socket host: %s', e.value)
        except conveyor.ipc.MissingPortException as e:
            code = 1
            self._log.error('missing socket port: %s', e.value)
        except conveyor.ipc.InvalidPortException as e:
            code = 1
            self._log.error('invalid socket port: %s', e.port)
        except conveyor.ipc.MissingPathException as e:
            code = 1
            self._log.error('missing socket path: %s', e.value)
        else:
            code = None
        return code

    def _run(self):
        raise NotImplementedError

    def _initeventqueue(self):
        value = self._config[self._configsection]['eventthreads']
        try:
            count = int(value)
        except ValueError:
            code = 1
            self._log.critical(
                'invalid value for "%s/eventthreads": %s', self._configsection,
                value)
        else:
            eventqueue = conveyor.event.geteventqueue()
            for i in range(count):
                name = 'eventqueue-%d' % (i,)
                thread = conveyor.event.EventQueueThread(eventqueue, name)
                thread.start()
                self._eventthreads.append(thread)

    def main(self, argv):
        self._unparsedargs = argv
        try:
            conveyor.debug.initdebug()
            try:
                code = self._sequence(*self._getstages())
            finally:
                conveyor.stoppable.StoppableManager.stopall()
                for thread in self._eventthreads:
                    thread.join(1)
                    if thread.is_alive():
                        self._log.debug('thread not terminated: %r', thread)
        except KeyboardInterrupt:
            code = 0
            self._log.warning('interrupted', exc_info=True)
        except SystemExit as e:
            code = e.code
            self._log.debug('handled exception', exc_info=True)
        except:
            code = 1
            self._log.critical('internal error', exc_info=True)
        if 0 == code:
            level = logging.INFO
        else:
            level = logging.ERROR
        self._log.log(
            level, '%s terminating with status code %d', self._program, code)
        conveyor.debug.logthreads(logging.DEBUG)
        return code

class _AbstractMainTestCase(unittest.TestCase):
    pass
