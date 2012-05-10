# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/client/__main__.py
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

import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.client
import conveyor.log
import conveyor.main

class _ClientMain(conveyor.main.AbstractMain):
    def __init__(self):
        conveyor.main.AbstractMain.__init__(self, 'conveyor')

    def _initparser(self):
        parser = conveyor.main.AbstractMain._initparser(self)
        for method in (
            self._initparser_logging,
            self._initparser_version,
            self._initparser_socket,
            self._initparser_subparsers,
            ):
                method(parser)
        return parser

    def _initparser_socket(self, parser):
        parser.add_argument(
            '-s'
            '--socket',
            default=None,
            type=str,
            required=True,
            help='the socket address',
            metavar='ADDRESS')

    def _initparser_subparsers(self, parser):
        subparsers = parser.add_subparsers(dest='command', title='Commands')
        for method in (
            self._initsubparser_print,
            self._initsubparser_printtofile,
            ):
                method(subparsers)

    def _initsubparser_print(self, subparsers):
        parser = subparsers.add_parser('print', help='print a .thing')
        parser.set_defaults(func=self._print)
        self._initparser_common(parser)

    def _initsubparser_printtofile(self, subparsers):
        parser = subparsers.add_parser('printtofile', help='print a .thing')
        parser.set_defaults(func=self._printtofile)
        self._initparser_common(parser)

    def _initparser_common(self, parser):
        for method in (
            self._initparser_logging,
            self._initparser_version,
            ):
                method(parser)
        parser.add_argument(
            '--toolpath-generator-bus-name',
            default='com.makerbot.ToolpathGenerator',
            required=False,
            help='set the D-Bus bus name for the toolpath generator',
            metavar='BUS-NAME',
            dest='toolpathgeneratorbusname')
        parser.add_argument(
            '--printer-bus-name',
            default='com.makerbot.Printer',
            required=False,
            help='set the D-Bus bus name for the printer',
            metavar='BUS-NAME',
            dest='printerbusname')
        parser.add_argument(
            'thing', help='print a .thing file', metavar='THING')

    def _run(self, parser, args):
        code = 0
        return code

    def _print(self, parser, args):
        pass

    def _printtofile(self, parser, args):
        pass

class _ClientMainTestCase(unittest.TestCase):
    pass

def _main(argv): # pragma: no cover
    conveyor.log.initlogging('conveyor')
    main = _ClientMain()
    code = main.main(argv)
    return code

if '__main__' == __name__: # pragma: no cover
    sys.exit(_main(sys.argv))
