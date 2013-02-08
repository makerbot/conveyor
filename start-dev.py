#! /usr/bin/env python
# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/start.py
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

'''A Python-based startup script for conveyor.'''

from __future__ import (absolute_import, print_function, unicode_literals)

import json
import os
import os.path
import subprocess
import sys

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
        action='store',
        type=str,
        required=False,
        help='read configuration from FILE',
        metavar='FILE',
        dest='config_file')
    parsed_args, unparsed_args = parser.parse_known_args(argv[1:])
    if None is parsed_args.config_file:
        parsed_args.config_file = 'conveyor-dev.conf'
    try:
        with open(parsed_args.config_file) as fp:
            config = json.load(fp)
    except ValueError:
        pid_file = 'conveyord.pid'
    else:
        pid_file = config.get('common', {}).get('pid_file', 'conveyord.pid')
    if os.path.exists(pid_file):
        print(
            'conveyor-start: pid file exists; is the conveyor service already running?',
            file=sys.stderr)
        return 1
    elif 'VIRTUAL_ENV' not in os.environ:
        print('conveyor-start: virtualenv is not activated', file=sys.stderr)
        return 1
    else:
        path = os.pathsep.join([
            os.path.join('src', 'main', 'python'),
            os.path.join(os.pardir, 's3g'),
            ])
        if 'PYTHONPATH' not in os.environ:
            os.environ['PYTHONPATH'] = path
        else:
            os.environ['PYTHONPATH'] = os.pathsep.join((
                path, os.environ['PYTHONPATH']))
        arguments = [
            'python',
            '-B',
            '-m', 'conveyor.server.__main__',
            '-c', parsed_args.config_file,
            ]
        if len(unparsed_args) > 0 and '--' == unparsed_args[0]:
            unparsed_args = unparsed_args[1:]
        arguments.extend(unparsed_args)
        os.execvp(sys.executable, arguments) # NOTE: this line does not return.


if '__main__' == __name__:
    code = _main(sys.argv)
    if None is code:
        code = 0
    sys.exit(code)
