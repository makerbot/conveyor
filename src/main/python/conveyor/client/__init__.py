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
            self._initsubparser_readeeprom,
            self._initsubparser_writeeeprom,
            self._initsubparser_getuploadablemachines,
            self._initsubparser_getmachineversions,
            self._initsubparser_downloadfirmware,
            self._initsubparser_uploadfirmware,
            self._initsubparser_resettofactory,
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
        parser.add_argument(
            '-j',
            '--json',
            action='store_true',
            default=False,
            help='use JSON output',
            dest='json')
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
            help='the path to the object file',
            metavar='INPUTPATH')
        parser.add_argument(
            '--skip-start-end',
            action='store_true',
            default=False,
            help='use start/end gcode provided by file')
        parser.add_argument(
            '--preprocessor',
            action='append',
            help='preprocessor to run on the gcode file',
            dest='preprocessor')
        parser.add_argument(
            '-m',
            '--material',
            default='PLA',
            choices=('ABS', 'PLA'),
            help='set the material',
            dest='material')
        parser.add_argument(
            '-s',
            '--slicer',
            default='miraclegrue',
            choices=('miraclegrue', 'skeinforge'),
            help='set the slicer (miraclegrue or skeinforge)',
            dest='slicer')

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
            action='append',
            help='preprocessor to run on the gcode file',
            dest='preprocessor')
        parser.add_argument(
            '-m',
            '--material',
            default='PLA',
            choices=('ABS', 'PLA'),
            help='set the material',
            dest='material')
        parser.add_argument(
            '-s',
            '--slicer',
            default='miraclegrue',
            choices=('miraclegrue', 'skeinforge'),
            help='set the slicer',
            dest='slicer')

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
            action='append',
            help='preprocessor to run on the gcode file',
            dest='preprocessor')
        parser.add_argument(
            '-m',
            '--material',
            default='PLA',
            choices=('ABS', 'PLA'),
            help='set the material',
            dest='material')
        parser.add_argument(
            '-s',
            '--slicer',
            default='miraclegrue',
            choices=('miraclegrue', 'skeinforge'),
            help='set the slicer',
            dest='slicer')

    def _initsubparser_getuploadablemachines(self, subparsers):
        parser = subparsers.add_parser(
            'getuploadablemachines',
            help='get list of machines we can upload to')
        parser.set_defaults(func=self._run_getuploadablemachines)
        self._initparser_common(parser)

    def _initsubparser_getmachineversions(self, subparsers):
        parser = subparsers.add_parser(
            'getmachineversions',
            help='get versions associated with this machine')
        parser.set_defaults(func=self._run_getmachineversions)
        self._initparser_common(parser)
        parser.add_argument(
            '--machinetype',
            default='TheReplicator',
            help='get version numbers associated with this machine',
            dest='machinetype')

    def _initsubparser_downloadfirmware(self, subparsers):
        parser = subparsers.add_parser(
            'downloadfirmware',
            help='download firmware')
        parser.set_defaults(func=self._run_downloadfirmware)
        self._initparser_common(parser)
        parser.add_argument(
            '--machinetype',
            default='TheReplicator',
            help='machine to upload to',
            dest='machinetype')
        parser.add_argument(
            '--machineversion',
            default='5.5',
            help='version to download',
            dest='version')

    def _initsubparser_uploadfirmware(self, subparsers):
        parser = subparsers.add_parser(
            'uploadfirmware',
            help='upload firmware to the bot')
        parser.set_defaults(func=self._run_uploadfirmware)
        self._initparser_common(parser)
        parser.add_argument(
            '--machinetype',
            default='TheReplicator',
            help='machine to upload to',
            dest='machinetype')
        parser.add_argument(
            'filename',
            help='firmware file to upload')

    def _initsubparser_readeeprom(self, subparsers):
        parser = subparsers.add_parser(
            'readeeprom',
            help="read a machine's eeprom")
        parser.set_defaults(func=self._run_readeeprom)
        self._initparser_common(parser)
        parser.add_argument(
            'outputpath',
            help='the output path for the read eeprom map',
            metavar='OUTPUTPATH')

    def _initsubparser_writeeeprom(self, subparsers):
        parser = subparsers.add_parser(
            'writeeeprom',
            help="write a json map to a machine's eeprom")
        parser.set_defaults(func=self._run_writeeeprom)
        self._initparser_common(parser)
        parser.add_argument(
            'inputpath',
            help="the path to the json eeprom map",
            metavar="INPUTPATH")

    def _initsubparser_resettofactory(self, subparsers):
        parser = subparsers.add_parser(
            'resettofactory',
            help="reset the machine's eeprom to factory settings",
            )
        parser.set_defaults(func=self._run_resettofactory)
        self._initparser_common(parser)

    def _run(self):
        self._log.debug('parsedargs=%r', self._parsedargs)
        self._initeventqueue()
        try:
            self._socket = self._address.connect()
        except EnvironmentError as e:
            code = 1
            self._log.critical(
                'failed to open socket: %s: %s',
                self._config['common']['address'], e.strerror, exc_info=True)
            if not self._lockfile_exists():
                self._log.critical(
                    'Unable to connect to conveyor server. Please verify that it is running.')
        else:
            code = self._parsedargs.func()
        return code

    def _run_resettofactory(self):
        params = {'printername' : None}
        code = self._run_client('resettofactory', params, False, None)
        return code

    def _run_getuploadablemachines(self):
        def display(result):
            print(result)
        params = {'printername' : None}
        code = self._run_client('getuploadablemachines', params, False, display)
        return code

    def _run_getmachineversions(self):
        def display(result):
            print(result)
        params = {'machine_type': self._parsedargs.machinetype}
        code = self._run_client('getmachineversions', params, False, display)
        return code

    def _run_downloadfirmware(self):
        params = {
            'machinetype': self._parsedargs.machinetype,
            'version': self._parsedargs.version
        }
        def display(result):
            self._log.info('downloaded firmware to: %s', result)
        code = self._run_client('downloadfirmware', params, False, display)
        return code

    def _run_uploadfirmware(self):
        params = {
            'printername': None,
            'machinetype': self._parsedargs.machinetype,
            'filename': self._parsedargs.filename,
        }
        code = self._run_client('uploadfirmware', params, False, None)
        return code

    def _run_readeeprom(self):
        outputpath = os.path.abspath(self._parsedargs.outputpath)
        def writeout(result):
            dumps = json.dumps(result, sort_keys=True, indent=2)
            with open(outputpath, 'w') as f:
                f.write(dumps)
        params = {
            'printername' : None,
            }
        code = self._run_client('readeeprom', params, False, writeout)
        return code

    def _run_writeeeprom(self):
        inputpath = os.path.abspath(self._parsedargs.inputpath)
        with open(inputpath) as f:
            eeprommap = json.load(f)
        params = {
            'printername' : None,
            'eeprommap' : eeprommap,
            }
        code = self._run_client('writeeeprom', params, False, None)
        return code

    def _run_cancel(self):
        params = {'id': int(self._parsedargs.jobid)}
        code = self._run_client('canceljob', params, False, None)
        return code

    def _run_dir(self):
        params = {}
        def display(result):
            if self._parsedargs.json:
                json.dump(result, sys.stdout)
                print()
            else:
                for methodname, description in result.items():
                    self._log.info('%s: %s', methodname, description)
        code = self._run_client('dir', params, False, display)
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
        if 'miraclegrue' == self._parsedargs.slicer:
            slicer = conveyor.domain.Slicer.MIRACLEGRUE
        elif 'skeinforge' == self._parsedargs.slicer:
            slicer = conveyor.domain.Slicer.SKEINFORGE
        else:
            raise ValueError(self._parsedargs.slicer)
        slicer_settings = conveyor.domain.SlicerConfiguration(
            slicer=slicer,
            extruder=0,
            raft=False,
            support=False,
            infill=0.1,
            layer_height=0.27,
            shells=2,
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

    def _lockfile_exists(self):
        result = os.path.isfile(self._config['common']['lockfile'])
        return result

class Client(object):
    @classmethod
    def clientFactory(cls, sock, method, params, wait, display):
        jsonrpc = conveyor.jsonrpc.JsonRpc(sock, sock)
        client = Client(sock, sock, jsonrpc, method, params, wait, display)
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
        self._stopped = False
        self._wait = wait # Wait for a job to complete (as opposed to a plain task)

    def _stop(self):
        self._stopped = True
        self._fp.stop()

    # TODO: !*@**#&... _jobchanged should take a single parameter called "job"
    # that has the job details, instead of all of the job contents as separate
    # parameters.  Can't fix this correctly yet since it will break the C++
    # binding...

    def _jobchanged(self, *args, **kwargs):
        if not self._stopped:
            job = conveyor.domain.Job.fromdict(kwargs)
            jobid = None
            if None is not self._job:
                jobid = self._job.id
            if None is not self._job and self._job.id == job.id:
                if conveyor.task.TaskState.STOPPED == job.state:
                    if conveyor.task.TaskConclusion.ENDED == job.conclusion:
                        self._log.info('job ended')
                        self._code = 0
                    elif conveyor.task.TaskConclusion.FAILED == job.conclusion:
                        self._log.error('job failed: %s', job.failure)
                        self._code = 1
                    elif conveyor.task.TaskConclusion.CANCELED == job.conclusion:
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
        if conveyor.task.TaskConclusion.CANCELED == task.conclusion:
            self._log.warning('canceled')
            self._code = 1
            self._stop()
        elif conveyor.task.TaskConclusion.FAILED == task.conclusion:
            self._log.error('%s', task.failure)
            self._code = 1
            self._stop()
        elif conveyor.task.TaskConclusion.ENDED == task.conclusion:
            if self._wait:
                # Record the job details and keep running (at least until the
                # server calls the jobchanged method).
                self._job = conveyor.domain.Job.fromdict(task.result)
            else:
                self._code = 0
                if None is not self._display:
                    self._display(task.result)
                self._stop()
        else:
            raise ValueError(task.conclusion)

    def run(self):
        self._jsonrpc.addmethod('jobchanged', self._jobchanged)
        task = self._jsonrpc.request("hello", {})
        task.stoppedevent.attach(self._hellocallback)
        task.start()
        try:
            self._jsonrpc.run()
        except IOError as e:
            if not self._stopped:
                raise
        return self._code
