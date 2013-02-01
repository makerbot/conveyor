#! /usr/bin/env python
# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/stop.py
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

'''A Python-based shutdown script for conveyor.'''

from __future__ import (absolute_import, print_function, unicode_literals)

import json
import os
import os.path
import signal
import sys
import time

try:
    # The argparse module was added to Python as of version 2.7. However, there
    # is a backport for older versions of Python and we expect that it is
    # installed into the virtualenv.
    import argparse
except ImportError:
    print(
        "conveyor-start: missing required module 'argparse'; is the virtualenv activated?",
        file=sys.stderr)
    sys.exit(1)


def _main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c',
        '--config',
        help='the configuration file',
        metavar='FILE')
    parsed_args, unparsed_args = parser.parse_known_args(argv[1:])
    if None is parsed_args.config:
        parsed_args.config = 'conveyor-dev.conf'
    try:
        with open(parsed_args.config) as fp:
            config = json.load(fp)
    except ValueError:
        pid_file = 'conveyord.pid'
    else:
        pid_file = config.get('common', {}).get('pid_file', 'conveyord.pid')
    if not os.path.exists(pid_file):
        print(
            'conveyor-stop: pid file not found; is the conveyor service already stopped?',
            file=sys.stderr)
        code = 1
    else:
        with open(pid_file) as fp:
            pid = int(fp.read())
        _graceful(pid)
        time.sleep(2)
        if os.path.exists(pid_file):
            _kill(pid)
        if not os.path.exists(pid_file):
            code = 0
        else:
            print(
                'conveyor-stop: shutdown signal sent but the pid file still exists',
                file=sys.stderr)
            code = 1
        return code


if not sys.platform.startswith('win'):

    #
    # Posix (a.k.a. not Windows)
    #

    def _graceful(pid):
        os.kill(pid, signal.SIGTERM)


    def _kill(pid):
        os.kill(pid, signal.SIGKILL)


else:

    #
    # Windows
    #

    import ctypes
    kernel32 = ctypes.windll.kernel32

    def _graceful(pid):
        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms681952%28v=vs.85%29.aspx
        dwProcessId = pid
        kernel32.AttachConsole(dwProcessId)

        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms686016%28v=vs.85%29.aspx
        HandlerRoutine = None
        Add = True
        kernel32.SetConsoleCtrlHandler(HandlerRoutine, Add)

        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms683155%28v=vs.85%29.aspx
        # dwCtrlEvent: 0=CTRL_C_EVENT, 1=CTRL_BREAK_EVENT
        dwCtrlEvent = 0
        dwProcessGroupId = 0
        kernel32.GenerateConsoleCtrlEvent(dwCtrlEvent, dwProcessGroupId)

    def _kill(pid):
        # Based on:
        # http://docs.python.org/2/faq/windows.html#how-do-i-emulate-os-kill-in-windows

        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms684320%28v=vs.85%29.aspx
        # dwDesiredAccess: 1=PROCESS_TERMINATE
        dwDesiredAccess = 1
        bInheritHandle = False
        dwProcessId = pid
        hProcess = kernel32.OpenProcess(dwDesiredAccess, bInheritHandle, dwProcessId)

        # http://msdn.microsoft.com/en-us/library/windows/desktop/ms686714%28v=vs.85%29.aspx
        uExitCode = 1
        kernel32.TerminateProcess(hProcess, uExitCode)


if '__main__' == __name__:
    code = _main(sys.argv)
    if None is code:
        code = 0
    sys.exit(code)
