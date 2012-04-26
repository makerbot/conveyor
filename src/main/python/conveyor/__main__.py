# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import argparse
import conveyor.async
import conveyor.printer.dbus
import conveyor.thing
import conveyor.toolpathgenerator.dbus
import dbus
import json
import logging
import logging.config
import os
import os.path
import sys
import tempfile
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
            version='%(prog)s 0.1.0.0')

    def _init_subparsers(self, parser):
        subparsers = parser.add_subparsers(
            dest='command',
            title='commands')
        for method in (
            self._init_subparsers_print,
            self._init_subparsers_printtofile,
            ):
                method(subparsers)

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
        self._init_parser_print_common(parser)

    def _init_subparsers_printtofile(self, subparsers):
        parser = subparsers.add_parser(
            'printtofile',
            help='print a .thing to an .s3g file')
        self._init_parser_common(parser)
        self._init_parser_print_common(parser)
        parser.add_argument(
            's3g_path',
            help='the output .s3g filename',
            metavar='S3G')

    def _command(self, args):
        if 'print' == args.command:
            method = self._command_print
        elif 'printtofile' == args.command:
            method = self._command_printtofile
        else:
            raise NotImplementedError
        code = method(args)
        return code

    def _command_print(self, args):
        def func(printer, input_path):
            async = printer.build(input_path)
            return async
        code = self._command_print_common(args, func)
        return code

    def _command_printtofile(self, args):
        def func(printer, input_path):
            output_path = os.path.abspath(args.s3g_path)
            async = printer.buildtofile(input_path, output_path)
            return async
        code = self._command_print_common(args, func)
        return code

    def _command_print_common(self, args, buildfunc):
        if not os.path.exists(args.thing_path):
            code = 1
            self._log.error('no such file or directory: %s', args.thing_path)
        elif not os.path.isdir(args.thing_path):
            code = 1
            self._log.error('unsupported file format: %s', args.thing_path)
        else:
            manifest_path = os.path.join(args.thing_path, 'manifest.json')
            if not os.path.exists(manifest_path):
                code = 1
                self._log.error(
                    'no such file or directory: %s', manifest_path)
            else:
                manifest = conveyor.thing.Manifest.from_path(manifest_path)
                manifest.validate()
                if 1 == len(manifest.instances):
                    code = self._print_single(args, manifest, buildfunc)
                elif 2 == len(manifest.instances):
                    code = self._print_dual(args, manifest, buildfunc)
                else:
                    raise Exception
        return code

    def _print_single(self, args, manifest, buildfunc):
        conveyor.async.set_implementation(
            conveyor.async.AsyncImplementation.QT)
        bus = dbus.SessionBus()
        toolpathgenerator = conveyor.toolpathgenerator.dbus._DbusToolpathGenerator.create(
            bus, args.toolpathgeneratorbusname)
        printer = conveyor.printer.dbus._DbusPrinter.create(
            bus, args.printerbusname)
        async_list = []
        for manifest_instance in manifest.instances.values(): # this loop is fishy; see _print_dual
            stl = os.path.abspath(os.path.join(manifest.base,
                manifest_instance.object.name))
            async1 = toolpathgenerator.stl_to_gcode(stl)
            async_list.append(async1)
            assert stl.endswith('.stl')
            gcode = ''.join((stl[:-4], '.gcode')) # perhaps not duplicate this everywhere
            async2 = buildfunc(printer, gcode)
            async_list.append(async2)
        async = conveyor.async.asyncsequence(async_list)
        async.wait()
        if async.state in (conveyor.async.AsyncState.SUCCESS,
            conveyor.async.AsyncState.CANCELED):
                code = 0
        else:
            code = 1
        return code

    def _print_dual(self, args, manifest, buildfunc):
        conveyor.async.set_implementation(conveyor.async.AsyncImplementation.QT)
        bus = dbus.SessionBus()
        toolpathgenerator = conveyor.toolpathgenerator.dbus._DbusToolpathGenerator.create(
            bus, args.toolpathgeneratorbusname)
        printer = conveyor.printer.dbus._DbusPrinter.create(
            bus, args.printerbusname)
        plastic_a_instance = self._get_plastic_a_instance(manifest)
        plastic_b_instance = self._get_plastic_b_instance(manifest)
        plastic_a_stl = os.path.abspath(os.path.join(manifest.base,
            plastic_a_instance.object.name))
        plastic_b_stl = os.path.abspath(os.path.join(manifest.base,
            plastic_b_instance.object.name))
        assert plastic_a_stl.endswith('.stl')
        assert plastic_b_stl.endswith('.stl')
        plastic_a_gcode = ''.join((plastic_a_stl[:-4], '.gcode'))
        plastic_b_gcode = ''.join((plastic_b_stl[:-4], '.gcode'))
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as tmp:
            merged_gcode = tmp.name
        os.unlink(merged_gcode)
        print('merged filename: %r' % (merged_gcode,))
        async1 = toolpathgenerator.stl_to_gcode(plastic_a_stl)
        async2 = toolpathgenerator.stl_to_gcode(plastic_b_stl)
        async3 = toolpathgenerator.merge_gcode(plastic_a_gcode,
            plastic_b_gcode, merged_gcode)
        async4 = buildfunc(printer, merged_gcode)
        async_list = [async1, async2, async3, async4]
        async = conveyor.async.asyncsequence(async_list)
        async.wait()
        print(async.state)
        if async.state in (conveyor.async.AsyncState.SUCCESS,
            conveyor.async.AsyncState.CANCELED):
                code = 0
        else:
            code = 1
        return code

    def _get_plastic_a_instance(self, manifest):
        for manifest_instance in manifest.instances.values():
            if 'plastic A' == manifest_instance.construction.name:
                return manifest_instance
        raise Exception

    def _get_plastic_b_instance(self, manifest):
        for manifest_instance in manifest.instances.values():
            if 'plastic B' == manifest_instance.construction.name:
                return manifest_instance
        raise Exception

def _main(argv):
    main = _Main()
    code = main.main(argv)
    return code

if '__main__' == __name__:
    sys.exit(_main(sys.argv))
