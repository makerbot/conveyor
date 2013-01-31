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

import lockfile.pidlockfile
import logging
import os
import signal
import sys

import conveyor
import conveyor.arg
import conveyor.log
import conveyor.main
import conveyor.machine
import conveyor.machine.port
import conveyor.server
import conveyor.spool

from conveyor.decorator import args


@args(conveyor.arg.nofork)
class ServerMain(conveyor.main.AbstractMain):
    _program_name = 'conveyord'

    _config_section = 'server'

    _logging_handlers = ['log',]

    def _run(self):
        has_daemon = False
        code = -17 #failed to run err
        try:
            import daemon
            import daemon.pidfile
            has_daemon = True
        except ImportError:
            self._log.debug('handled exception', exc_info=True)
        def handle_sigterm(signum, frame):
            self._log.info('received signal %d', signum)
            sys.exit(0)
        pidfile = self._config.get('common', 'pid_file')
        try:
            if self._parsed_args.nofork or not has_daemon:
                for signal_name in ('SIGTERM', 'SIGBREAK'):
                    if hasattr(signal, signal_name):
                        signal.signal(
                            getattr(signal, signal_name), handle_sigterm)
                lock = lockfile.pidlockfile.PIDLockFile(pidfile)
                lock.acquire(0)
                try:
                    code = self._run_server()
                finally:
                    lock.release()
            else:
                files_preserve = list(conveyor.log.getfiles())
                dct = {
                    'files_preserve': files_preserve,
                    'pidfile': daemon.pidfile.TimeoutPIDLockFile(pidfile, 0)
                }
                if not self._config.get('server', 'chdir'):
                    dct['working_directory'] = os.getcwd()
                context = daemon.DaemonContext(**dct)
                # The daemon module's implementation of terminate() raises a
                # SystemExit with a string message instead of an exit code. This
                # monkey patch fixes it.
                context.terminate = handle_sigterm # monkey patch!
                with context:
                    code = self._run_server()
        except lockfile.AlreadyLocked:
            self._log.debug('handled exception', exc_info=True)
            self._log.error('pid file exists: %s', pidfile)
            code = 1
        except lockfile.UnlockError:
            self._log.warning('error while removing pidfile', exc_info=True)
        return code

    def _run_server(self):
        self._log_startup(logging.INFO)
        self._init_event_threads()
        driver_manager = conveyor.machine.DriverManager.create(self._config)
        port_manager = conveyor.machine.port.PortManager.create(
            driver_manager)
        machine_manager = conveyor.machine.MachineManager()
        spool = conveyor.spool.Spool()
        connection_manager = conveyor.server.ConnectionManager(
            machine_manager, spool)
        address = self._config.get('common', 'address')
        listener = address.listen()
        with listener:
            server = conveyor.server.Server(
                self._config, driver_manager, port_manager, machine_manager,
                spool, connection_manager, listener)
            code = server.run()
            return code


def _main(argv): # pragma: no cover
    conveyor.log.earlylogging('conveyord')
    main = ServerMain()
    code = main.main(argv)
    if None is code:
        code = 0
    return code


if '__main__' == __name__: # pragma: no cover
    sys.exit(_main(sys.argv))
