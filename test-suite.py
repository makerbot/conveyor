#! /usr/bin/env python
# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/test-suite.py
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

'''A Python-based test suite script for conveyor.'''

from __future__ import (absolute_import, print_function, unicode_literals)

import os
import os.path
import subprocess
import sys


_MODULES = [
    'conveyor',
    'conveyor.client',
    'conveyor.debug',
    'conveyor.enum',
    'conveyor.event',
    'conveyor.jsonrpc',
    'conveyor.log',
    'conveyor.main',
    'conveyor.process',
    'conveyor.recipe',
    'conveyor.server',
    'conveyor.stoppable',
    'conveyor.task',
    'conveyor.test',
    'conveyor.slicer',
    'conveyor.slicer.miraclegrue',
    'conveyor.slicer.skeinforge',
    'conveyor.visitor',
    'pi_test_Address',
    'pi_test_stoppable',
    ]


def _main(argv):
    main_path = os.path.join('src', 'main', 'python')
    test_path = os.path.join('src', 'test', 'python')
    pythonpath = os.pathsep.join([
        main_path,
        test_path,
        os.path.join(os.pardir, 's3g'),
        ])
    if 'PYTHONPATH' not in os.environ:
        os.environ['PYTHONPATH'] = pythonpath
    else:
        os.environ['PYTHONPATH'] = os.pathsep.join([
            pythonpath, os.environ['PYTHONPATH']])
    def generator():
        for dirpath, dirnames, filenames in os.walk(main_path):
            for filename in filenames:
                if filename.endswith('.py'):
                    yield os.path.join(dirpath, filename)
    include = ','.join(generator())
    subprocess.check_call(['coverage', 'erase'])
    code = subprocess.call(['coverage', 'run', '--branch', 'test.py', '--', '-v'] + _MODULES)
    subprocess.check_call(['coverage', 'annotate', '-d', 'obj', '--include', include])
    subprocess.check_call(['coverage', 'html', '-d', 'obj', '--include', include])
    subprocess.check_call(['coverage', 'xml', '-o', os.path.join('obj', 'coverage.xml'), '--include', include])
    subprocess.check_call(['coverage', 'report', '-m', '--include', include])
    return code


if '__main__' == __name__:
    code = _main(sys.argv[1:])
    if None is code:
        code = 0
    sys.exit(code)
