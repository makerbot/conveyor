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
import logging
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.ipc

class AbstractMain(object):
    def __init__(self, program):
        self._log = logging.getLogger(self.__class__.__name__)
        self._program = program

    def _getaddress(self, value):
        address = None
        try:
            address = conveyor.ipc.getaddress(value)
        except conveyor.ipc.UnknownProtocolException as e:
            self._log.error('unknown socket protocol: %s', e.protocol)
        except conveyor.ipc.MissingHostException as e:
            self._log.error('missing socket host: %s', e.value)
        except conveyor.ipc.MissingPortException as e:
            self._log.error('missing socket port: %s', e.value)
        except conveyor.ipc.InvalidPortException as e:
            self._log.error('invalid socket port: %s', e.port)
        except conveyor.ipc.MissingPathException as e:
            self._log.error('missing socket path: %s', e.value)
        return address

    def _initparser(self):
        parser = argparse.ArgumentParser(prog=self._program)
        def error(message):
            self._log.error(message)
            sys.exit(1)
        parser.error = error # monkey patch!
        return parser

    def _initparser_logging(self, parser):
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

    def _initparser_version(self, parser):
        parser.add_argument(
            '-v',
            '--version',
            action='version',
            help='show the version message and exit',
            version='%(prog)s 0.1.0.0')

    def _run(self, parser, args):
        raise NotImplementedError

    def main(self, argv):
        try:
            parser = self._initparser()
            args = parser.parse_args(argv[1:])
            if args.level:
                root = logging.getLogger()
                root.setLevel(args.level)
            self._log.debug('args=%r', args)
            code = self._run(parser, args)
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
        return code

class _AbstractMainTestCase(unittest.TestCase):
    def test__run(self):
        main = AbstractMain()
        with self.assertRaises(NotImplementedError):
            main._run()
