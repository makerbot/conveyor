# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import argparse
import logging
import logging.config
import os.path
import sys
try:
    import unittest2 as unittest
except ImportError:
    import unittest

class _Main(object):
    def __init__(self):
        self._log = None

    def main(self, argv):
        self._init_logging()
        self._log = logging.getLogger('conveyor.__main__._Main')
        try:
            parser = self._init_parser()
            args = parser.parse_args(argv[1:])
            if args.level:
                logger = logging.getLogger()
                logger.setLevel(args.level)
            self._log.debug('main: args=%r', args)
            code = self._command(args)
        except SystemExit, e:
            code = e.code
        except:
            self._log.exception('unhandled exception')
            code = 1
        if 0 == code:
            level = logging.INFO
        else:
            level = logging.ERROR
        self._log.log(level, 'conveyor terminating with status code %d', code)
        return code

    def _init_logging(self):
        for path in ('logging.ini',):
            if self._init_logging_file(path):
                return
        self._init_logging_basic()

    def _init_logging_file(self, path):
        if not os.path.exists(path):
            success = False
        else:
            with open(path, 'r') as file:
                logging.config.fileConfig(file)
            success = True
        return success

    def _init_logging_basic(self):
        logging.basicConfig(
            format='conveyor: %(levelname)s: %(message)s',
            datefmt='%Y.%m.%d|%H:%M:%S',
            level=logging.INFO)

    def _init_parser(self):
        parser = argparse.ArgumentParser(prog='conveyor')
        def error(message):
            self._log.error(message)
            sys.exit(1)
        parser.error = error # monkey patch!
        for method in (
            self._init_parser_common,
            self._init_parser_version,
            self._init_subparsers,
            ):
                method(parser)
        return parser

    def _init_parser_common(self, parser):
        for method in (
            self._init_parser_common_logging,
            ):
                method(parser)

    def _init_parser_common_logging(self, parser):
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

    def _init_parser_version(self, parser):
        parser.add_argument(
            '-v',
            '--version',
            action='version',
            help='show the version message and exit',
            version='%(prog) 0.1.0.0')

    def _init_subparsers(self, parser):
        subparsers = parser.add_subparsers(
            dest='command',
            title='commands')
        for method in (
            ):
                method(subparsers)

    def _command(self, args):
        raise NotImplementedError

def _main(argv):
    main = _Main()
    code = main.main(argv)
    return code

if '__main__' == __name__:
    sys.exit(_main(sys.argv))
