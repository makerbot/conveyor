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
import time

import conveyor.arg
import conveyor.domain
import conveyor.jsonrpc
import conveyor.main
import conveyor.task
import conveyor.main

from conveyor.decorator import args, command


class _ClientCommand(conveyor.main.Command):
    '''A client command.'''


class _ConnectionCommand(_ClientCommand):
    '''A client command that requires a connection to the conveyor service.'''

    def __init__(self, parsed_args, config):
        _ClientCommand.__init__(self, parsed_args, config)
        self._jsonrpc = None
        self._stop = False
        self._code = 0

    def run(self):
        address = self._config.get('common', 'address')
        try:
            self._connection = address.connect()
        except EnvironmentError as e:
            self._code = 1
            self._log.critical(
                'failed to connect to address: %s: %s',
                address, e.strerror, exc_info=True)
            if not self._pid_file_exists():
                self._log.critical(
                    'pid file missing; is the conveyor service running?')
        else:
            self._jsonrpc = conveyor.jsonrpc.JsonRpc(
                self._connection, self._connection)
            self._export_methods()
            hello_task = self._jsonrpc.request('hello', {})
            hello_task.stoppedevent.attach(self._hello_callback_wrapper)
            hello_task.start()
            self._jsonrpc.run()
        return self._code

    def _pid_file_exists(self):
        pid_file = self._config.get('common', 'pid_file')
        result = os.path.exists(pid_file)
        return result

    def _export_methods(self):
        '''
        Export JSON-RPC methods to the conveyor service. The default
        implementation does not export any methods.

        '''

    def _hello_callback_wrapper(self, hello_task):
        '''
        A callback wrapper that calls `_check_task` before calling
        `_hello_callback`. This reduces some repetitive code.

        '''

        if self._check_task(hello_task):
            self._hello_callback(hello_task)

    def _hello_callback(self, hello_task):
        '''
        A callback invoked after the command successfully invokes `hello` on
        the conveyor service. This callback can be used to invoke additional
        methods on the conveyor service.

        '''
        raise NotImplementedError

    def _check_task(self, task):
        '''
        Returns whether or not a task ended successfully. It terminates the
        client if the task failed or was canceled.

        '''

        if conveyor.task.TaskConclusion.ENDED == task.conclusion:
            result = True
        elif conveyor.task.TaskConclusion.FAILED == task.conclusion:
            self._code = 1
            self._log.error('%s', task.failure)
            self._stop_jsonrpc()
            result = False
        elif conveyor.task.TaskConclusion.CANCELED == task.conclusion:
            self._code = 1
            self._log.warning('canceled')
            self._stop_jsonrpc()
            result = False
        else:
            raise ValueError(task.conclusion)
        return result

    def _stop_jsonrpc(self):
        '''Stop the JSON-RPC connection. This will end the client.'''
        self._stop = True
        self._jsonrpc.stop()


class _MethodCommand(_ConnectionCommand):
    '''
    A client command that invokes a JSON-RPC request or notification on the
    conveyor service.

    '''

    def _hello_callback(self, hello_task):
        method_task = self._create_method_task()
        method_task.stoppedevent.attach(self._method_callback)
        method_task.start()

    def _create_method_task(self):
        '''Creates a task for a request to be invoked on the conveyor service.'''
        raise NotImplementedError

    def _method_callback(self, method_task):
        '''
        A callback invoked when the request returns. This callback can be used
        to handle the result of the request, to handle errors, and to invoke
        additional methods on the conveyor service.

        '''
        raise NotImplementedError


class _QueryCommand(_MethodCommand):
    '''
    A client command that invokes a JSON-RPC request on the conveyor service
    and handles the result.

    '''

    def _method_callback(self, method_task):
        if self._check_task(method_task):
            self._handle_result(method_task.result)
            self._stop_jsonrpc()

    def _handle_result(self, result):
        '''Handles the result of the query.'''
        raise NotImplementedError


@args(conveyor.arg.json)
class _JsonCommand(_QueryCommand):
    '''
    A client command that invokes a JSON-RPC request on the conveyor service
    and optionally prints the result in raw JSON format.

    '''

    def _handle_result(self, result):
        if self._parsed_args.json:
            self._handle_result_json(result)
        else:
            self._handle_result_default(result)

    def _handle_result_json(self, result):
        '''Handles the result of the query by printing it in raw JSON format.'''
        json.dump(result, sys.stdout)
        print()

    def _handle_result_default(self, result):
        '''
        Handles the result of the query in some way other than printing it in
        raw JSON format.

        '''
        raise NotImplementedError


class _MonitorCommand(_MethodCommand):
    '''
    A client command that invokes a JSON-RPC request on the conveyor service
    and waits for a job to complete. The request must return a job id.

    '''

    def __init__(self, parsed_args, config):
        _JsonCommand.__init__(self, parsed_args, config)
        self._job_id = None

    def _export_methods(self):
        self._jsonrpc.addmethod('jobchanged', self._job_changed)

    def _job_changed(self, *args, **kwargs):
        '''
        Invoked by the conveyor service to inform the client that a job has
        changed.

        '''

        job = conveyor.domain.Job.fromdict(kwargs)
        if (not self._stop and None is not self._job_id
                and self._job_id == job_id):
            if conveyor.task.TaskState.STOPPED == job.state:
                if conveyor.task.TaskConclusion.ENDED == job.conclusion:
                    self._code = 0
                    self._log.info('job ended')
                elif conveyor.task.TaskConclusion.FAILED == job.conclusion:
                    self._code = 1
                    self._log.error('job failed: %s', job.failure)
                elif conveyor.task.TaskConclusion.CANCELED == job.conclusion:
                    self._code = 1
                    self._log.warning('job canceled')
                else:
                    raise ValueError(job.conclusion)
                self._stop_jsonrpc()

    def _method_callback(self, method_task):
        if self._check_task(method_task):
            if (None is not method_task.result
                    and isinstance(method_task.result, dict)
                    and 'id' in method_task.result):
                self._job_id = method_task.result['id']
            else:
                self._code = 1
                self._log.error(
                    'the conveyor service returned invalid job information')
                self._stop_jsonrpc()


@args(conveyor.arg.job)
class _CancelCommand(_MethodCommand):
    name = 'cancel'

    help = 'cancel a job'

    def _create_method_task(self):
        params = {'id': self._parsed_args.job_id}
        method_task = self._jsonrpc.request('canceljob', params)
        return method_task

    def _method_callback(self, method_task):
        if self._check_task(method_task):
            self._stop_jsonrpc()


@args(conveyor.arg.firmware_version)
class _CompatibleFirmware(_QueryCommand):
    name = 'compatiblefirmware'

    help = 'determine if a firmware verison is comatible with the MakerBot driver'

    def _create_method_task(self):
        params = {'firmwareversion': self._parsed_args.firmware_version}
        method_task = self._jsonrpc.request('compatiblefirmware', params)
        return method_task

    def _handle_result(self, result):
        print('Your firmware version is compatible: %r' % (result,))


class _DirCommand(_JsonCommand):
    name = 'dir'

    help = 'list the methods available from the conveyor service'

    def _create_method_task(self):
        params = {}
        method_task = self._jsonrpc.request('dir', params)
        return method_task

    def _handle_result_default(self, result):
        for method_name, description in result.items():
            self._log.info('%s: %s', method_name, description)


@args(conveyor.arg.machine_type)
@args(conveyor.arg.machine_version)
class _DownloadFirmware(_QueryCommand):
    name = 'downloadfirmware'

    help = 'download firmware'

    def _create_method_task(self, result):
        params = {
            'machinetype': self._parsed_args.machine_type,
            'version': self._parsed_args.machine_version,
        }
        method_task = self._jsonrpc.request('downloadfirmware', params)
        return method_task

    def _handle_result(self, result):
        self._log.info('firmware downloaded to: %s', result)


@args(conveyor.arg.machine_type)
class _GetMachineVersions(_QueryCommand):
    name = 'getmachineversions'

    help = 'get the firmware versions available for a machine'

    def _create_method_task(self):
        params = {'machine_type': self._parsed_args.machine_type}
        method_task = self._jsonrpc.request('getmachineversions', params)
        return method_task

    def _handle_result(self, result):
        self._log.info('%s', result)


class _GetUploadableMachines(_QueryCommand):
    name = 'getuploadablemachines'

    help = 'list the machines to which conveyor can upload firmware'

    def _create_method_task(self):
        params = {}
        method_task = self._jsonrpc.request('getuploadablemachines', params)
        return method_task

    def _handle_result(self, result):
        print(result)


@args(conveyor.arg.job)
class _JobCommand(_JsonCommand):
    name = 'job'

    help = 'get the details for a job'

    def _create_method_task(self):
        params = {'id': int(self._parsed_args.job_id)}
        method_task = self._jsonrpc.request('getjob', params)
        return method_task

    def _handle_result_default(self, result):
        self._log.info('%s', result)


class _JobsCommand(_JsonCommand):
    name = 'jobs'

    help = 'get the details for all jobs'

    def _create_method_task(self):
        params = {}
        method_task = self._jsonrpc.request('getjobs', params)
        return method_task

    def _handle_result_default(self, result):
        self._log.info('%s', result)


@args(conveyor.arg.extruder)
@args(conveyor.arg.gcode_processor)
@args(conveyor.arg.has_start_end)
@args(conveyor.arg.material)
@args(conveyor.arg.slicer)
@args(conveyor.arg.slicer_settings)
@args(conveyor.arg.input_file)
class _PrintCommand(_MonitorCommand):
    name = 'print'

    help = 'print an object'

    def _create_method_task(self):
        slicer_settings = _create_slicer_settings(self._parsed_args)
        slicer_settings.path = self._parsed_args.slicer_settings_path
        params = {
            'printername': None,
            'inputpath': os.path.abspath(self._parsed_args.input_file),
            'gcodeprocessor': self._parsed_args.gcode_processor,
            'material': self._parsed_args.material_name,
            'skip_start_end': self._parsed_args.has_start_end,
            'archive_lvl': 'all',
            'archive_dir': None,
            'slicer_settings': slicer_settings.todict(),
        }
        method_task = self._jsonrpc.request('print', params)
        return method_task


@args(conveyor.arg.extruder)
@args(conveyor.arg.gcode_processor)
@args(conveyor.arg.file_type)
@args(conveyor.arg.has_start_end)
@args(conveyor.arg.material)
@args(conveyor.arg.slicer)
@args(conveyor.arg.slicer_settings)
@args(conveyor.arg.input_file)
@args(conveyor.arg.output_file)
class _PrintToFileCommand(_MonitorCommand):
    name = 'printtofile'

    help = 'print an object to an .s3g or .x3g file'

    def _create_method_task(self):
        slicer_settings = _create_slicer_settings(self._parsed_args)
        slicer_settings.path = self._parsed_args.slicer_settings_path
        params = {
            'profilename': None,
            'inputpath': os.path.abspath(self._parsed_args.input_file),
            'outputpath': os.path.abspath(self._parsed_args.output_file),
            'gcodeprocessor': self._parsed_args.gcode_processor,
            'material': self._parsed_args.material_name,
            'skip_start_end': self._parsed_args.has_start_end,
            'archive_lvl': 'all',
            'archive_dir': None,
            'slicer_settings': slicer_settings.todict(),
            'print_to_file_type': self._parsed_args.file_type,
        }
        method_task = self._jsonrpc.request('print', params)
        return method_task


class _PrintersCommand(_JsonCommand):
    name = 'printers'

    help = 'list connected printers'

    def _create_method_task(self):
        params = {}
        method_task = self._jsonrpc.request('printers', params)
        return method_task

    def _handle_result_default(self, result):
        for dct in result:
            printer = conveyor.domain.Printer.fromdict(dct)
            self._log.info('Printer:')
            self._log.info('  display name: %s', printer.display_name)
            self._log.info('  unique name: %s', printer.unique_name)
            self._log.info('  printer type: %s', printer.printer_type)
            self._log.info('  firmware version: %s', printer.firmware_version)
            self._log.info('  can print: %s', printer.can_print)
            self._log.info('  can print to file: %s', printer.can_printtofile)
            self._log.info('  heated platform: %s', printer.has_heated_platform)
            self._log.info('  number of toolheads: %s', printer.number_of_toolheads)
            self._log.info('  connection status: %s', printer.connection_status)


@args(conveyor.arg.output_file)
class _ReadEepromCommand(_QueryCommand):
    name = 'reeadeeprom'

    help = 'read a machine EEPROM'

    def _create_method_task(self):
        params = {'printername': None}
        method_task = self._jsonrpc.request('readeeprom', params)
        return method_task

    def _handle_result(self, result):
        output_file = os.path.abspath(self._parsed_args.output_file)
        with open(output_file, 'w') as fp:
            json.dump(result, fp, sort_keys=True, indent=2)


class _ResetToFactoryCommand(_QueryCommand):
    name = 'resettofactory'

    help = 'reset a machine EEPROM to factory settings'

    def _create_method_task(self):
        params = {'printername', None}
        method_task = self._jsonrpc.request('resettofactory', params)
        return method_task

    def _handle_result(self, result):
        pass


@args(conveyor.arg.add_start_end)
@args(conveyor.arg.extruder)
@args(conveyor.arg.gcode_processor)
@args(conveyor.arg.material)
@args(conveyor.arg.slicer)
@args(conveyor.arg.slicer_settings)
@args(conveyor.arg.input_file)
@args(conveyor.arg.output_file)
class _SliceCommand(_MonitorCommand):
    name = 'slice'

    help = 'slice an object to a .gcode file'

    def _create_method_task(self):
        slicer_settings = _create_slicer_settings(self._parsed_args)
        slicer_settings.path = self._parsed_args.slicer_settings_path
        params = {
            'profilename': None,
            'inputpath': os.path.abspath(self._parsed_args.input_file),
            'outputpath': os.path.abspath(self._parsed_args.output_file),
            'gcodeprocessor': self._parsed_args.gcode_processor,
            'material': self._parsed_args.material_name,
            'with_start_end': self._parsed_args.add_start_end,
            'slicer_settings': slicer_settings.todict(),
        }
        method_task = self._jsonrpc.request('slice', params)
        return method_task


@args(conveyor.arg.machine_type)
@args(conveyor.arg.input_file)
class _UploadFirmwareCommand(_QueryCommand):
    name = 'uploadfirmware'

    help = 'upload firmware'

    def _create_method_task(self):
        params = {
            'printername': None,
            'machinetype': self._parsedargs.machine_type,
            'filename': self._parsedargs.input_file,
        }
        method_task = self._jsonrpc.request('uploadfirmware', params)
        return method_task

    def _handle_result(self, result):
        pass


@args(conveyor.arg.input_file)
class _VerifyS3gCommand(_QueryCommand):
    name = 'verifys3g'

    help = 'verify an s3g/x3g file.'

    def _create_method_task(self):
        params = {'s3gpath': self._parsed_args.input_file}
        method_task = self._jsonrpc.request('verifys3g', params)
        return method_task

    def _handle_result(self, result):
        print('Your s3g file is %s valid' % ('NOT' if result is False else '',))


class _WaitForServiceCommand(_ClientCommand):
    name = 'waitforservice'

    help = 'wait for the conveyor service to start'

    def run(self):
        now = time.time()
        failtime = now + 30.0
        address = self._config.get('common', 'address')
        while True:
            try:
                address.connect()
            except:
                now = time.time()
                if now < failtime:
                    time.sleep(1.0)
                else:
                    self._log.error('failed to connect to conveyor service')
                    code = 1
                    break
            else:
                self._log.info('connected')
                code = 0
                break
        return code


@args(conveyor.arg.input_file)
class _WriteEepromCommand(_QueryCommand):
    name = 'writeeeprom'

    help = 'write a machine EEPROM'

    def _create_method_task(self):
        input_file = os.path.abspath(self._parsed_args.input_file)
        with open(input_file) as fp:
            eeprommap = json.load(fp)
        params = {
            'printername': None,
            'eeprommap': eeprommap,
        }
        method_task = self._jsonrpc.request('writeeeprommap', params)
        return method_task

    def _handle_result(self, result):
        pass


def _create_slicer_settings(parsed_args):
    if 'miraclegrue' == parsed_args.slicer_name:
        slicer = conveyor.domain.Slicer.MIRACLEGRUE
    elif 'skeinforge' == parsed_args.slicer_name:
        slicer = conveyor.domain.Slicer.SKEINFORGE
    else:
        raise ValueError(parsed_args.slicer_name)
    if 'right' == parsed_args.extruder_name:
        extruder = '0'
    elif 'left' == parsed_args.extruder_name:
        extruder = '1'
    elif 'both' == parsed_args.extruder_name:
        extruder = '0,1'
    else:
        raise ValueError(parsed_args.extruder)
    slicer_settings = conveyor.domain.SlicerConfiguration(
        slicer=slicer,
        extruder=extruder,
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
