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
            self._initparser_logging,
            self._initparser_version,
            self._initparser_socket,
            ):
                method(parser)
        return parser

    def _initparser_socket(self, parser):
        parser.add_argument(
            'socket',
            default=None,
            type=str,
            help='the socket address',
            metavar='ADDRESS')

    def _run(self, parser, args):
        address = self._getaddress(args.socket)
        if None == address:
            code = 1
        else:
            sock = address.listen()
            server = conveyor.server.Server(sock)
            code = server.run()
        return code

class _ServerMainTestCase(unittest.TestCase):
    pass

def _main(argv): # pragma: no cover
    conveyor.log.initlogging('conveyord')
    main = _ServerMain()
    code = main.main(argv)
    return code

if '__main__' == __name__: # pragma: no cover
    sys.exit(_main(sys.argv))
