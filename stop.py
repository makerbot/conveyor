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
    with open(parsed_args.config) as fp:
        config = json.load(fp)
    pidfile = config['common']['pidfile']
    if not os.path.exists(pidfile):
        print(
            'conveyor-stop: pid file not found; is the conveyor service already stopped?',
            file=sys.stderr)
        code = 1
    else:
        with open(pidfile) as fp:
            try:
                pid = int(fp.read())
            except ValueError:
                pid = None
        if 'nt' == os.name:
            sig = signal.CTRL_C_EVENT
        else:
            sig = signal.SIGTERM
        os.kill(pid, sig) # Politely ask the daemon to stop.
        time.sleep(1)
        if os.path.exists(pidfile):
            if 'nt' == os.name:
                sig = 0
            else:
                sig = signal.SIGKILL
            os.kill(pid, sig) # Murder the daemon!
        if not os.path.exists(pidfile):
            code = 0
        else:
            print(
                'conveyor-stop: shutdown signal sent but the pid file still exists',
                file=sys.stderr)
            code = 1
        return code


if '__main__' == __name__:
    code = _main(sys.argv)
    if None is code:
        code = 0
    sys.exit(code)
