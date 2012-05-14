# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/server/__main__.py
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
import json
import logging.config
import os
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.log
import conveyor.main
import conveyor.server

class _ServerMain(conveyor.main.AbstractMain):
    def __init__(self):
        conveyor.main.AbstractMain.__init__(self, 'conveyord')

    def _initparser(self):
        parser = conveyor.main.AbstractMain._initparser(self)
        for method in (
            self._initparser_config,
            self._initparser_logging,
            self._initparser_nofork,
            self._initparser_version,
            ):
                method(parser)
        return parser

    def _initparser_config(self, parser):
        parser.add_argument(
            '-c',
            '--config',
            default='/etc/conveyor/conveyord.conf',
            type=str,
            help='the configuration file',
            metavar='FILE')

    def _initparser_nofork(self, parser):
        parser.add_argument(
            '--nofork',
            action='store_true',
            default=False,
            help='do not fork nor detach from the terminal')

    def _setdefaults(self, config):
        config.setdefault('pidfile', '/var/run/conveyor/conveyord.pid')
        config.setdefault('chdir', True)
        config.setdefault('socket', 'unix:/var/run/conveyor/conveyord.socket')

    def _run(self, parser, args):
        try:
            with open(args.config, 'r') as fp:
                config = json.load(fp)
        except EnvironmentError as e:
            code = 1
            self._log.critical(
                'failed to open configuration file: %s: %s', args.config,
                e.strerror, exc_info=True)
        except ValueError:
            code = 1
            self._log.critical(
                'failed to parse configuration file: %s', args.config,
                exc_info=True)
        else:
            self._setdefaults(config)
            if args.nofork:
                code = self._run_server(args, config)
            else:
                try:
                    import daemon
                    import lockfile.pidlockfile
                except ImportError:
                    self._log.debug('handled exception', exc_info=True)
                    code = self._run_server(args, config)
                else:
                    pidfile = config['pidfile']
                    dct = {
                        'pidfile': lockfile.pidlockfile.PIDLockFile(pidfile)
                    }
                    if not config['chdir']:
                        dct['working_directory'] = os.getcwd()
                    context = daemon.DaemonContext(**dct)
                    def terminate(signal_number, stack_frame):
                        # The daemon module's implementation of terminate()
                        # raises a SystemExit with a string message instead of
                        # an exit code. This monkey patch fixes it.
                        sys.exit(0)
                    context.terminate = terminate # monkey patch!
                    with context:
                        code = self._run_server(args, config)
        return code

    def _run_server(self, args, config):
        try:
            dct = config.get('logging')
            if None is not dct:
                dct['incremental'] = False
                dct['disable_existing_loggers'] = False
                logging.config.dictConfig(dct)
                if args.level:
                    root = logging.getLogger()
                    root.setLevel(args.level)
        except ValueError as e:
            code = 1
            self._log.critical(
                'invalid logging configuration: %s', e.message, exc_info=True)
        else:
            self._log.info('starting conveyord')
            value = config['socket']
            address = self._getaddress(value)
            if None == address:
                code = 1
            else:
                with address:
                    try:
                        sock = address.listen()
                    except EnvironmentError as e:
                        code = 1
                        self._log.critical(
                            'failed to open socket: %s: %s', value,
                            e.strerror, exc_info=True)
                    else:
                        server = conveyor.server.Server(sock)
                        code = server.run()
        return code

class _ServerMainTestCase(unittest.TestCase):
    pass

def _main(argv): # pragma: no cover
    conveyor.log.earlylogging('conveyord')
    main = _ServerMain()
    code = main.main(argv)
    return code

if '__main__' == __name__: # pragma: no cover
    sys.exit(_main(sys.argv))
