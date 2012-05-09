# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import argparse
import logging
import logging.config
import os.path
import socket
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.client
import conveyor.ipc
import conveyor.log
import conveyor.server

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
            self._log.debug('args=%r', args)
            code = self._command(parser, args)
        except KeyboardInterrupt:
            self._log.warning('interrupted', exc_info=True)
            code = 0
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
        self._init_logging_default()

    def _init_logging_file(self, path):
        if not os.path.exists(path):
            success = False
        else:
            with open(path, 'r') as file:
                logging.config.fileConfig(file)
            success = True
        return success

    def _init_logging_default(self):
        dct = {
            'version': 1,
            'formatters': {
                'log': {
                    '()': 'conveyor.log.DebugFormatter',
                    'format': '%(asctime)s - %(levelname)s - %(message)s',
                    'datefmt': '%Y.%m.%d - %H:%M:%S',
                    'debugformat': '%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(funcName)s - %(message)s'
                },
                'console': {
                    '()': 'conveyor.log.ConsoleFormatter',
                    'format': 'conveyor: %(levelname)s: %(message)s'
                },
            },
            'filters': {
                'stdout': {
                    '()': 'conveyor.log.StdoutFilter'
                },
                'stderr': {
                    '()': 'conveyor.log.StderrFilter'
                }
            },
            'handlers': {
                'stdout': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'console',
                    'filters': ['stdout'],
                    'stream': sys.stdout
                },
                'stderr': {
                    'class': 'logging.StreamHandler',
                    'level': 'WARNING',
                    'formatter': 'console',
                    'filters': ['stderr'],
                    'stream': sys.stderr
                },
                'log': {
                    'class': 'logging.FileHandler',
                    'level': 'NOTSET',
                    'formatter': 'log',
                    'filters': [],
                    'filename': 'conveyor.log'
                }
            },
            'loggers': {},
            'root': {
                'level': 'INFO',
                'propagate': True,
                'filters': [],
                'handlers': ['stdout', 'stderr', 'log']
            },
            'incremental': False,
            'disable_existing_loggers': True
        }
        logging.config.dictConfig(dct)

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

    def _init_parser_socket(self, parser):
        parser.add_argument(
            '-s',
            '--socket',
            default=None,
            type=str,
            required=True,
            help='set the socket address',
            metavar='ADDRESS')

    def _init_parser_version(self, parser):
        parser.add_argument(
            '-v',
            '--version',
            action='version',
            help='show the version message and exit',
            version='%(prog)s 0.1.0.0')

    def _init_subparsers(self, parser):
        subparsers = parser.add_subparsers(
            dest='command',
            title='commands')
        for method in (
            self._init_subparsers_daemon,
            self._init_subparsers_print,
            self._init_subparsers_printtofile,
            ):
                method(subparsers)

    def _init_subparsers_daemon(self, subparsers):
        parser = subparsers.add_parser(
            'daemon',
            help='daemonize')
        self._init_parser_common(parser)
        self._init_parser_socket(parser)

    def _init_parser_print_common(self, parser):
        parser.add_argument(
            'thing_path',
            help='the URL for a .thing resource',
            metavar='THING')
        parser.add_argument(
            '--toolpath-generator-bus-name',
            default='com.makerbot.ToolpathGenerator',
            required=False,
            help='set the DBus bus name for the toolpath generator',
            metavar='BUS-NAME',
            dest='toolpathgeneratorbusname')
        parser.add_argument(
            '--printer-bus-name',
            default='com.makerbot.Printer',
            required=False,
            help='set the DBus bus name for the printer',
            metavar='BUS-NAME',
            dest='printerbusname')

    def _init_subparsers_print(self, subparsers):
        parser = subparsers.add_parser(
            'print',
            help='print a .thing')
        self._init_parser_common(parser)
        self._init_parser_socket(parser)
        self._init_parser_print_common(parser)

    def _init_subparsers_printtofile(self, subparsers):
        parser = subparsers.add_parser(
            'printtofile',
            help='print a .thing to an .s3g file')
        self._init_parser_common(parser)
        self._init_parser_socket(parser)
        self._init_parser_print_common(parser)
        parser.add_argument(
            's3g_path',
            help='the output .s3g filename',
            metavar='S3G')

    def _command(self, parser, args):
        if 'daemon' == args.command:
            method = self._command_daemon
        elif 'print' == args.command:
            method = self._command_print
        elif 'printtofile' == args.command:
            method = self._command_printtofile
        else:
            raise NotImplementedError
        code = method(parser, args)
        return code

    def _command_daemon(self, parser, args):
        sock = conveyor.ipc.getsocket(args.socket)
        if None is sock:
            code = 1
        else:
            s = sock.listen()
            server = conveyor.server.Server(s)
            code = server.run()
        return code

    def _command_print(self, parser, args):
        sock = conveyor.ipc.getsocket(args.socket)
        if None is sock:
            code = 1
        else:
            s = sock.connect()
            client = conveyor.client.Client.create(s, 'print', [])
            code = client.run()
        return code

    def _command_printtofile(self, parser, args):
        sock = self._getsocket(args)
        if None is sock:
            code = 1
        else:
            s = sock.connect()
            client = conveyor.client.Client.create(s, 'printtofile', [])
            code = client.run()
        return code

def _main(argv):
    main = _Main()
    code = main.main(argv)
    return code

if '__main__' == __name__:
    sys.exit(_main(sys.argv))
