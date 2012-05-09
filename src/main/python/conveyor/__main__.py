# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import argparse
import dbus
import json
import logging
import logging.config
import os
import os.path
import socket
import sys
import tempfile
import threading
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.client
import conveyor.event
import conveyor.jsonrpc
import conveyor.printer.dbus
import conveyor.server
import conveyor.thing
import conveyor.toolpathgenerator.dbus

class _Socket(object):
    def listen(self):
        raise NotImplementedError

    def connect(self):
        raise NotImplementedError

class _TcpSocket(_Socket):
    def __init__(self, host, port):
        self._host = host
        self._port = port

    def listen(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self._host, self._port))
        s.listen(socket.SOMAXCONN)
        return s

    def connect(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self._host, self._port))
        return s

class _UnixSocket(_Socket):
    def __init__(self, path):
        self._path = path

    def listen(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(self._path)
        s.listen(socket.SOMAXCONN)
        return s

    def connect(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self._path)
        return s

class _DebugFormatter(object):
    def __init__(self, format, datefmt, debugformat):
        self._formatter = logging.Formatter(format, datefmt)
        self._debugformatter = logging.Formatter(debugformat, datefmt)

    def format(self, record):
        if logging.DEBUG != record.levelno:
            result = self._formatter.format(record)
        else:
            result = self._debugformatter.format(record)
        return result

    def formatTime(self, record, datefmt=None):
        if logging.DEBUG != record.levelno:
            result = self._formatter.formatTime(record, datefmt)
        else:
            result = self._debugformatter.formatTime(record, datefmt)
        return result

    def formatException(self, exc_info):
        if logging.DEBUG != record.levelno:
            result = self._formatter.formatException(exc_info)
        else:
            result = self._debugformatter.formatException(exc_info)
        return result

class _StdoutFilter(object):
    def filter(self, record):
        result = (record.levelno == logging.INFO)
        return result

class _StderrFilter(object):
    def filter(self, record):
        result = (record.levelno >= logging.WARNING)
        return result

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
            code = self._command(parser, args)
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
                    '()': 'conveyor.__main__._DebugFormatter',
                    'format': '%(asctime)s - %(levelname)s - %(message)s',
                    'datefmt': '%Y.%m.%d - %H:%M:%S',
                    'debugformat': '%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(funcName)s - %(message)s'
                },
                'console': {
                    'format': '%(levelname)s - %(message)s'
                },
            },
            'filters': {
                'stdout': {
                    '()': 'conveyor.__main__._StdoutFilter'
                },
                'stderr': {
                    '()': 'conveyor.__main__._StderrFilter'
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
                    'level': 'ERROR',
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

    def _getsocket(self, args):
        split = args.socket.split(':', 1)
        if 'tcp' == split[0]:
            if 2 != len(split):
                self._log.error('invalid TCP socket: %s', args.socket)
                sock = None
            else:
                host_port = split[1].split(':', 1)
                if 2 != len(host_port):
                    self._log.error('invalid TCP socket: %s', args.socket)
                    sock = None
                else:
                    host = host_port[0]
                    try:
                        port = int(host_port[1])
                    except ValueError:
                        self._log.error('invalid TCP port: %s', host_port[1])
                    else:
                        self._log.debug('TCP socket: host=%r, port=%r', host, port)
                        sock = _TcpSocket(host, port)
        elif 'unix' == split[0]:
            if 2 != len(split):
                self._log.error('invalid UNIX socket: %s', args.socket)
                sock = None
            else:
                path = split[1]
                self._log.debug('UNIX socket: path=%r', path)
                sock = _UnixSocket(path)
        else:
            self._log.error('unknown socket type: %s', split[0])
            sock = None
        return sock

    def _command_daemon(self, parser, args):
        sock = self._getsocket(args)
        if None is sock:
            code = 1
        else:
            s = sock.listen()
            server = conveyor.server.Server(s)
            code = server.run()
        return code

    def _command_print(self, parser, args):
        sock = self._getsocket(args)
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
