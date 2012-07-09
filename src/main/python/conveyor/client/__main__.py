# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/client/__main__.py
#
# conveyor - Printing dispatch engine for 3D objects and their friends.
# Copyright ¬© 2012 Matthew W. Samsonoff <matthew.samsonoff@makerbot.com>
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

import json
import sys


import conveyor.client
import conveyor.log
import conveyor.main.ClientMain as ClientMain

class _ClientMain(conveyor.main.AbstractMain):
    def __init__(self):
        conveyor.main.AbstractMain.__init__(self, 'conveyor', 'client')

    def _initparser_common(self, parser):
        conveyor.main.AbstractMain._initparser_common(self, parser)

    def _initsubparsers(self):
        subparsers = self._parser.add_subparsers(dest='command', title='Commands')
        for method in (
            self._initsubparser_print,
            self._initsubparser_printers,
            self._initsubparser_printtofile,
            self._initsubparser_slice,
            ):
                method(subparsers)

    def _initsubparser_printers(self, subparsers):
        parser = subparsers.add_parser('printers', help='list connected printers')
        parser.set_defaults(func=self._run_printers)
        self._initparser_common(parser)
        parser.add_argument(
            '--json',
            action='store_true',
            default=False,
            help='print in JSON format')

    def _initsubparser_print(self, subparsers):
        parser = subparsers.add_parser('print', help='print an object')
        parser.set_defaults(func=self._run_print)
        self._initparser_common(parser)
        parser.add_argument(
            'thing', help='the path to the object file', metavar='PATH')
        parser.add_argument(
            '--preprocessor',
            dest='preprocessor',
            default=False,
            help='preprocessor to run on gcode file.')
        parser.add_argument('--skip-start-end', action='store_true', default=False, help='use start/end gcode provided by file')

    def _initsubparser_printtofile(self, subparsers):
        parser = subparsers.add_parser('printtofile', help='print an object to an .s3g file')
        parser.set_defaults(func=self._run_printtofile)
        self._initparser_common(parser)
        parser.add_argument(
            'thing', help='the path to the object file', metavar='PATH')
        parser.add_argument(
            's3g', help='the output path for the .s3g file', metavar='S3G')
        parser.add_argument(
            '--preprocessor',
            dest='preprocessor',
            default=False,
            help='preprocessor to run on gcode file.')
        parser.add_argument('--skip-start-end', action='store_true', default=False, help='use start/end gcode provided by file')

    def _initsubparser_slice(self, subparsers):
        parser = subparsers.add_parser('slice', help='slice an object into .gcode')
        parser.set_defaults(func=self._run_slice)
        self._initparser_common(parser)
        parser.add_argument(
            'thing', help='the path to the object file', metavar='PATH')
        parser.add_argument(
            'gcode', help='the output path for the .gcode file',
            metavar='GCODE')
        parser.add_argument(
            '--preprocessor',
            dest='preprocessor',
            default=False,
            help='preprocessor to run on gcode file.')
        parser.add_argument('--with-start-end', action='store_true', default=False, help='append start and end gcode to .gcode file')

    def _run(self):
        self._initeventqueue()
        try:
            self._socket = self._address.connect()
        except EnvironmentError as e:
            code = 1
            self._log.critical(
                'failed to open socket: %s: %s',
                self._config['common']['socket'], e.strerror, exc_info=True)
        else:
            code = self._parsedargs.func()
        return code

    def _run_print(self):
        params = [self._parsedargs.thing, self._parsedargs.preprocessor, self._parsedargs.skip_start_end]
        self._log.info('printing: %s', self._parsedargs.thing)
        code = self._run_client('print', params)
        return code

    def _run_printers(self):
        printers = [
            {
                'name': 'bot 1',
                'displayname': 'Bot 1',
                'kind': 'Replicator',
                'extruders': 2,
                'printtofile': True
            },
            {
                'name': 'bot 2',
                'displayname': 'Bot 2',
                'kind': 'Replicator',
                'extruders': 2,
                'printtofile': True
            }
        ]
        if self._parsedargs.json:
            json.dump(printers, sys.stdout)
            print('')
        else:
            for i, printer in enumerate(printers):
                if 0 != i:
                    print('')
                print('Name: %s' % (printer['name'],))
                print('Display Name: %s' % (printer['displayname'],))
                print('Kind: %s' % (printer['kind'],))
                print('Extruders: %s' % (printer['extruders'],))
                print('Print to File: %s' % (printer['printtofile'],))
        return 0

    def _run_printtofile(self):
        params = [self._parsedargs.thing, self._parsedargs.s3g, self._parsedargs.preprocessor, self._parsedargs.skip_start_end]
        self._log.info(
            'printing to file: %s -> %s', self._parsedargs.thing,
            self._parsedargs.s3g)
        code = self._run_client('printtofile', params)
        return code

    def _run_slice(self):
        params = [self._parsedargs.thing, self._parsedargs.gcode, self._parsedargs.preprocessor, self._parsedargs.with_start_end]
        self._log.info(params)
        self._log.info(
            'slicing to file: %s -> %s', self._parsedargs.thing,
            self._parsedargs.gcode)
        code = self._run_client('slice', params)
        return code

    def _run_client(self, method, params):
        client = conveyor.client.Client.create(self._socket, method, params)
        code = client.run()
        return code

class _ClientMainTestCase(unittest.TestCase):
    pass

def _main(argv): # pragma: no cover
    conveyor.log.earlylogging('conveyor')
    main = ClientMain()
    code = main.main(argv)
    return code

if '__main__' == __name__: # pragma: no cover
    sys.exit(_main(sys.argv))
