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
        conveyor.main.AbstractMain.__init__(self, 'conveyord', 'server')

    def _initparser_common(self, parser):
        conveyor.main.AbstractMain._initparser_common(self, parser)
        parser.add_argument(
            '--nofork',
            action='store_true',
            default=False,
            help='do not fork nor detach from the terminal')

    def _initsubparsers(self):
        return None

    def _run(self):
        if self._parsedargs.nofork:
            code = self._run_server()
        else:
            try:
                import daemon
                import daemon.pidfile
            except ImportError:
                self._log.debug('handled exception', exc_info=True)
                code = self._run_server()
            else:
                files_preserve = list(conveyor.log.getfiles())
                pidfile = self._config['server']['pidfile']
                dct = {
                    'files_preserve': files_preserve,
                    'pidfile': daemon.pidfile.TimeoutPIDLockFile(pidfile, 0)
                }
                if not self._config['server']['chdir']:
                    dct['working_directory'] = os.getcwd()
                context = daemon.DaemonContext(**dct)
                def terminate(signal_number, stack_frame):
                    # The daemon module's implementation of terminate()
                    # raises a SystemExit with a string message instead of
                    # an exit code. This monkey patch fixes it.
                    sys.exit(0)
                context.terminate = terminate # monkey patch!
                with context:
                    code = self._run_server()
        return code

    def _run_server(self):
        self._initeventqueue()
        with self._address:
            self._socket = self._address.listen()
            server = conveyor.server.Server(self._config, self._socket)
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
