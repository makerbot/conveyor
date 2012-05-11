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

import socket
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
        self._initparser_logging(parser)
        self._initparser_version(parser)
        self._initparser_socket(parser, False)
        self._initparser_subparsers(parser)
        return parser

    def _initparser_socket(self, parser, required):
        parser.add_argument(
            '-s',
            '--socket',
            default=None,
            type=str,
            required=required,
            help='the socket address',
            metavar='ADDRESS')

    def _initparser_subparsers(self, parser):
        subparsers = parser.add_subparsers(dest='command', title='Commands')
        self._initsubparser_print(subparsers)
        self._initsubparser_printtofile(subparsers)

    def _initsubparser_print(self, subparsers):
        parser = subparsers.add_parser('print', help='print a .thing')
        parser.set_defaults(func=self._print)
        self._initparser_common(parser)

    def _initsubparser_printtofile(self, subparsers):
        parser = subparsers.add_parser('printtofile', help='print a .thing')
        parser.set_defaults(func=self._printtofile)
        self._initparser_common(parser)
        parser.add_argument(
            's3g', help='the output path for the .s3g file', metavar='S3G')

    def _initparser_common(self, parser):
        self._initparser_logging(parser)
        self._initparser_version(parser)
        self._initparser_socket(parser, True)
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
            'thing', help='the path to the .thing file', metavar='THING')

    def _run(self, parser, args):
        code = args.func(args)
        return code

    def _print(self, args):
        params = [
            args.toolpathgeneratorbusname, args.printerbusname, args.thing]
        code = self._client(args, 'print', params)
        return code

    def _printtofile(self, parser, args):
        params = [
            args.toolpathgeneratorbusname, args.printerbusname, args.thing,
            args.s3g]
        code = self._client(args, 'printtofile', params)
        return code

    def _client(self, args, method, params):
        address = self._getaddress(args.socket)
        if None == address:
            code = 1
        else:
            try:
                sock = address.connect()
            except socket.error as e:
                code = 1
                self._log.critical('failed to connect: %s', e, exc_info=True)
            else:
                client = conveyor.client.Client.create(sock, method, params)
                code = client.run()
        return code

class _ClientMainTestCase(unittest.TestCase):
    pass

def _main(argv): # pragma: no cover
    conveyor.log.initlogging('conveyor')
    main = _ClientMain()
    code = main.main(argv)
    return code

if '__main__' == __name__: # pragma: no cover
    sys.exit(_main(sys.argv))
