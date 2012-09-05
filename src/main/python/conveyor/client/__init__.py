# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/client/__init__.py
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

import json
import logging
import os.path
import socket
import sys
import tempfile

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.domain
import conveyor.jsonrpc
import conveyor.main
import conveyor.task
import conveyor.main

class ClientMain(conveyor.main.AbstractMain):
    def __init__(self):
        conveyor.main.AbstractMain.__init__(self, 'conveyor', 'client')

    def _initparser_common(self, parser):
        conveyor.main.AbstractMain._initparser_common(self, parser)

    def _initsubparsers(self):
        subparsers = self._parser.add_subparsers(
            dest='command',
            title='Commands')
        for method in (
            self._initsubparser_cancel,
            self._initsubparser_dir,
            self._initsubparser_job,
            self._initsubparser_jobs,
            self._initsubparser_print,
            self._initsubparser_printers,
            self._initsubparser_printtofile,
            self._initsubparser_slice,
        ):
                method(subparsers)

    def _initsubparser_cancel(self, subparsers):
        parser = subparsers.add_parser(
            'cancel',
            help='cancel a job')
        parser.set_defaults(func=self._run_cancel)
        self._initparser_common(parser)
        parser.add_argument(
            'jobid',
            type=int,
            help='the ID of the job to cancel',
            metavar='JOB')

    def _initsubparser_dir(self,subparsers):
        parser = subparsers.add_parser(
            'dir',
            help='list the methods available in the conveyor service')
        parser.set_defaults(func=self._run_dir)
        self._initparser_common(parser)

    def _initsubparser_job(self, subparsers):
        parser = subparsers.add_parser(
            'job',
            help='get the details for a job')
        parser.set_defaults(func=self._run_job)
        self._initparser_common(parser)
        parser.add_argument(
            'jobid',
            type=int,
            help='the job ID',
            metavar='JOB')

    def _initsubparser_jobs(self, subparsers):
        parser = subparsers.add_parser(
            'jobs',
            help='get the details for all jobs')
        parser.set_defaults(func=self._run_jobs)
        self._initparser_common(parser)

    def _initsubparser_print(self, subparsers):
        parser = subparsers.add_parser(
            'print',
            help='print an object')
        parser.set_defaults(func=self._run_print)
        self._initparser_common(parser)
        parser.add_argument(
            'inputpath',
            help='the path to the object file', metavar='INPUTPATH')
        parser.add_argument(
            '--skip-start-end',
            action='store_true',
            default=False,
            help='use start/end gcode provided by file')
        parser.add_argument(
            '--preprocessor',
            default=False,
            help='preprocessor to run on the gcode file',
            dest='preprocessor')
        parser.add_argument(
            '-m',
            '--material',
            default='PLA',
            help='Material to print with',
            dest='material')

    def _initsubparser_printers(self, subparsers):
        parser = subparsers.add_parser(
            'printers',
            help='list connected printers')
        parser.set_defaults(func=self._run_printers)
        parser.add_argument(
            '-j',
            '--json',
            action='store_true',
            default=False,
            help='use JSON output',
            dest='json')
        self._initparser_common(parser)
 
    def _initsubparser_printtofile(self, subparsers):
        parser = subparsers.add_parser(
            'printtofile',
            help='print an object to an .s3g file')
        parser.set_defaults(func=self._run_printtofile)
        self._initparser_common(parser)
        parser.add_argument(
            'inputpath',
            help='the path to the object file',
            metavar='INPUTPATH')
        parser.add_argument(
            'outputpath',
            help='the output path for the .s3g file',
            metavar='OUTPUTPATH')
        parser.add_argument(
            '--skip-start-end',
            action='store_true',
            default=False,
            help='use start/end gcode provided by file')
        parser.add_argument(
            '--preprocessor',
            default=False,
            help='preprocessor to run on the gcode file',
            dest='preprocessor')
        parser.add_argument(
            '-m',
            '--material',
            default='PLA',
            help='Material to print with',
            dest='material')

    def _initsubparser_slice(self, subparsers):
        parser = subparsers.add_parser(
            'slice',
            help='slice an object into .gcode')
        parser.set_defaults(func=self._run_slice)
        self._initparser_common(parser)
        parser.add_argument(
            'inputpath',
            help='the path to the object file',
            metavar='INPUTPATH')
        parser.add_argument(
            'outputpath',
            help='the output path for the .gcode file',
            metavar='OUTPUTPATH')
        parser.add_argument(
            '--with-start-end',
            action='store_true',
            default=False,
            help='include start and end gcode in .gcode file')
        parser.add_argument(
            '--preprocessor',
            default=False,
            help='preprocessor to run on the gcode file',
            dest='preprocessor')
        parser.add_argument(
            '-m',
            '--material',
            default='PLA',
            help='Material to print with',
            dest='material')

    def _run(self):
        self._initeventqueue()
        try:
            self._socket = self._address.connect()
        except EnvironmentError as e:
            code = 1
            self._log.critical(
                'failed to open socket: %s: %s',
                self._config['common']['socket'], e.strerror, exc_info=True)
            if not self._has_daemon_lock():
              self._log.critical(
                'Unable to connect to conveyor server. Please verify that it is running.')
        else:
            code = self._parsedargs.func()
        return code

    def _run_cancel(self):
        params = {'id': int(self._parsedargs.jobid)}
        code = self._run_client('canceljob', params, False, None)
        return code

    def _run_dir(self):
        self._log.error('dir not implemented')
        code = 1
        return code

    def _run_job(self):
        params = {'id': int(self._parsedargs.jobid)}
        def display(result):
            self._log.info('%s', result)
        code = self._run_client('getjob', params, False, display)
        return code

    def _run_jobs(self):
        params = {}
        def display(result):
            self._log.info('%s', result)
        code = self._run_client('getjobs', params, False, display)
        return code

    def _createslicerconfiguration(self):
        slicer_settings = conveyor.domain.SlicerConfiguration(
            slicer=conveyor.domain.Slicer.MIRACLEGRUE,
            extruder=0,
            raft=False,
            support=False,
            infill=0.1,
            layer_height=0.27,
            shells=1,
            extruder_temperature=230.0,
            platform_temperature=110.0,
            print_speed=80.0,
            travel_speed=100.0)
        return slicer_settings

    def _run_print(self):
        slicer_settings = self._createslicerconfiguration()
        params = {
            'printername': None,
            'inputpath': os.path.abspath(self._parsedargs.inputpath),
            'preprocessor': self._parsedargs.preprocessor,
            'material': self._parsedargs.material,
            'skip_start_end': self._parsedargs.skip_start_end,
            'archive_lvl': 'all',
            'archive_dir': None,
            'slicer_settings': slicer_settings.todict(),
        }
        self._log.info('printing: %s', self._parsedargs.inputpath)
        code = self._run_client('print', params, True, None)
        return code

    def _run_printers(self):
        def display(result):
            if self._parsedargs.json:
                json.dump(result, sys.stdout)
                print()
            else:
                for dct in result:
                    printer = conveyor.domain.Printer.fromdict(dct)
                    self._log.info('Printer:')
                    self._log.info('  display name: %s', printer.display_name)
                    self._log.info('  unique name: %s', printer.unique_name)
                    self._log.info('  printer type: %s', printer.printer_type)
                    self._log.info('  can print: %s', printer.can_print)
                    self._log.info('  can print to file: %s', printer.can_printtofile)
                    self._log.info('  heated platform: %s', printer.has_heated_platform)
                    self._log.info('  number of toolheads: %s', printer.number_of_toolheads)
                    self._log.info('  connection status: %s', printer.connection_status)
        params = {}
        code = self._run_client('getprinters', params, False, display)
        return code

    def _run_printtofile(self):
        slicer_settings = self._createslicerconfiguration()
        params = {
            'profilename': None,
            'inputpath': os.path.abspath(self._parsedargs.inputpath),
            'outputpath': os.path.abspath(self._parsedargs.outputpath),
            'preprocessor': self._parsedargs.preprocessor,
            'material':self._parsedargs.material,
            'skip_start_end': self._parsedargs.skip_start_end,
            'archive_lvl': 'all',
            'archive_dir': None,
            'slicer_settings': slicer_settings.todict(),
        }
        self._log.info(
            'printing to file: %s -> %s', self._parsedargs.inputpath,
            self._parsedargs.outputpath)
        code = self._run_client('printtofile', params, True, None)
        return code

    def _run_slice(self):
        slicer_settings = self._createslicerconfiguration()
        params = {
            'profilename': None,
            'inputpath': os.path.abspath(self._parsedargs.inputpath),
            'outputpath': os.path.abspath(self._parsedargs.outputpath),
            'preprocessor': self._parsedargs.preprocessor,
            'material':self._parsedargs.material,
            'with_start_end': self._parsedargs.with_start_end,
            'slicer_settings': slicer_settings.todict(),
        }
        self._log.info(
            'slicing to file: %s -> %s', self._parsedargs.inputpath,
            self._parsedargs.outputpath)
        code = self._run_client('slice', params, True, None)
        return code

    def _run_client(self, method, params, wait, display):
        client = conveyor.client.Client.clientFactory(
            self._socket, method, params, wait, display)
        code = client.run()
        return code

    def _has_daemon_lock(self):
        result = os.path.isfile(self._config['common']['daemon_lockfile'])
        return result

class Client(object):
    @classmethod
    def clientFactory(cls, sock, method, params, wait, display):
        fp = conveyor.jsonrpc.socketadapter(sock)
        jsonrpc = conveyor.jsonrpc.JsonRpc(fp, fp)
        client = Client(sock, fp, jsonrpc, method, params, wait, display)
        return client

    def __init__(self, sock, fp, jsonrpc, method, params, wait, display):
        self._code = None
        self._display = display
        self._fp = fp
        self._job = None
        self._jsonrpc = jsonrpc
        self._log = logging.getLogger(self.__class__.__name__)
        self._method = method
        self._params = params
        self._sock = sock
        self._wait = wait # Wait for a job to complete (as opposed to a plain task)

    def _stop(self):
        self._fp.stop()

    def _notify(self, job, state, conclusion):
        self._log.debug('job=%r, state=%r, conclusion=%r', job, state, conclusion)
        if conveyor.task.TaskState.STOPPED == state:
            if conveyor.task.TaskConclusion.ENDED == conclusion:
                self._code = 0
            elif conveyor.task.TaskConclusion.FAILED == conclusion:
                self._log.error('job failed')
                self._code = 1
            elif conveyor.task.TaskConclusion.CANCELED == conclusion:
                self._log.warning('job canceled')
                self._code = 1
            else:
                raise ValueError(task.conclusion)
            self._stop()

    def _hellocallback(self, task):
        self._log.debug('task=%r', task)
        if (conveyor.task.TaskConclusion.ENDED != task.conclusion
            or 'world' != task.result):
                self._log.error('failed to connect with conveyor')
                self._code = 1
                self._stop()
        else:
            task1 = self._jsonrpc.request(self._method, self._params)
            task1.stoppedevent.attach(self._methodcallback)
            task1.start()

    def _methodcallback(self, task):
        self._log.debug('task=%r', task)
        if self._wait:
            # Record the job details and keep running (at least until the
            # server calls the notify method).
            self._job = task.result
        else:
            if conveyor.task.TaskConclusion.ENDED != task.conclusion:
                self._code = 1
                self._log.error('%s', task.failure)
            else:
                self._code = 0
                if None is not self._display:
                    self._display(task.result)
            self._stop()

    def run(self):
        self._jsonrpc.addmethod('notify', self._notify)
        task = self._jsonrpc.request("hello", {})
        task.stoppedevent.attach(self._hellocallback)
        task.start()
        self._jsonrpc.run()
        return self._code
