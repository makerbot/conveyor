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

import itertools
import json
import logging
import os.path
import socket
import sys
import tempfile
import textwrap
import time

import conveyor.arg
import conveyor.domain
import conveyor.job
import conveyor.jsonrpc
import conveyor.main
import conveyor.slicer
import conveyor.machine.port
import conveyor.main
import conveyor.task

from conveyor.decorator import args, command


class _ClientCommand(conveyor.main.Command):
    '''A client command.'''

    def _get_driver_name(self):
        if None is not self._parsed_args.driver_name:
            driver_name = self._parsed_args.driver_name
        else:
            driver_name = self._config.get('client', 'driver')
        return driver_name

    def _get_profile_name(self):
        if None is not self._parsed_args.profile_name:
            profile_name = self._parsed_args.profile_name
        else:
            profile_name = self._config.get('client', 'profile')
        return profile_name


class _JsonRpcCommand(_ClientCommand):
    '''
    A client command that requires a JSON-RPC connection to the conveyor
    service.

    '''

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
            hello_task.stoppedevent.attach(
                self._guard_callback(self._hello_callback))
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

    def _guard_callback(self, callback):
        '''
        Creates a new callback that invokes `_check_task` and then invokes
        `callback` only if `_check_task` returns `True`. This reduces some
        repetitive code.

        '''
        def guard(task):
            if self._check_task(task):
                def func():
                    try:
                        callback(task)
                    except:
                        self._stop_jsonrpc()
                        raise
                conveyor.error.guard(self._log, func)
        return guard

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
            self._stop_jsonrpc()
            raise ValueError(task.conclusion)
        return result

    def _stop_jsonrpc(self):
        '''Stop the JSON-RPC connection. This will end the client.'''
        self._stop = True
        self._jsonrpc.stop()

    def _hello_callback(self, hello_task):
        '''
        A callback invoked after the command successfully invokes `hello` on
        the conveyor service. This callback can be used to invoke additional
        methods on the conveyor service.

        '''
        raise NotImplementedError


class _MethodCommand(_JsonRpcCommand):
    '''
    A client command that invokes a JSON-RPC request on the conveyor service.

    '''

    def _hello_callback(self, hello_task):
        method_task = self._create_method_task()
        method_task.stoppedevent.attach(
            self._guard_callback(self._method_callback))
        method_task.start()

    def _create_method_task(self):
        '''
        Creates a task for a request to be invoked on the conveyor service.

        '''

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
        '''
        Handles the result of the query by printing it in raw JSON format.

        '''
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
        _MethodCommand.__init__(self, parsed_args, config)
        self._job_id = None

    def _export_methods(self):
        self._jsonrpc.addmethod('jobchanged', self._job_changed)

    def _job_changed(self, *args, **kwargs):
        '''
        Invoked by the conveyor service to inform the client that a job has
        changed.

        '''

        job = conveyor.job.JobInfo.from_dict(kwargs)
        job_id = job.id
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
        if (None is not method_task.result
                and isinstance(method_task.result, dict)
                and 'id' in method_task.result):
            self._job_id = method_task.result['id']
        else:
            self._code = 1
            self._log.error(
                'the conveyor service returned invalid job information')
            self._stop_jsonrpc()


@args(conveyor.arg.driver)
@args(conveyor.arg.machine)
@args(conveyor.arg.port)
@args(conveyor.arg.profile)
class _ConnectedCommand(_MonitorCommand):
    '''
    A client command that connects a machine, invokes a JSON-RPC request on the
    conveyor service and waits for a job to complete. The request must return a
    job id.

    This is essentially a `_MonitorCommand` that calls `connect` on the
    conveyor service before invoking the job-related method. `connect` must
    return a `MachineInfo` object with a `name` field. The machine's name is
    stored in an instance field called `_machine_name`.

    '''

    def __init__(self, parsed_args, config):
        _MonitorCommand.__init__(self, parsed_args, config)
        self._machine_name = None

    def _hello_callback(self, hello_task):
        # NOTE: this method doesn't use the `_get_driver_name` nor
        # `_get_profile_name` as the driver and profile can often be detected
        # automatically.
        params = {
            'machine_name': self._parsed_args.machine_name,
            'port_name': self._parsed_args.port_name,
            'driver_name': self._parsed_args.driver_name,
            'profile_name': self._parsed_args.profile_name,
            'persistent': False,
        }
        connect_task = self._jsonrpc.request('connect', params)
        connect_task.stoppedevent.attach(
            self._guard_callback(self._connect_callback))
        connect_task.start()

    def _connect_callback(self, connect_task):
        self._machine_name = connect_task.result['name']
        method_task = self._create_method_task()
        method_task.stoppedevent.attach(
            self._guard_callback(self._method_callback))
        method_task.start()


@args(conveyor.arg.positional_job)
class CancelCommand(_MethodCommand):
    name = 'cancel'

    help = 'cancel a job'

    def _create_method_task(self):
        params = {'id': self._parsed_args.job_id}
        method_task = self._jsonrpc.request('canceljob', params)
        return method_task

    def _method_callback(self, method_task):
        self._stop_jsonrpc()


@args(conveyor.arg.driver)
@args(conveyor.arg.positional_firmware_version)
class CompatibleFirmware(_QueryCommand):
    name = 'compatiblefirmware'

    help = 'determine if a firmware verison is comatible with the MakerBot driver'

    def _create_method_task(self):
        params = {
            'driver_name': self._get_driver_name(),
            'firmware_version': self._parsed_args.firmware_version,
        }
        method_task = self._jsonrpc.request('compatiblefirmware', params)
        return method_task

    def _handle_result(self, result):
        print('Your firmware version is compatible: %r' % (result,))


@args(conveyor.arg.driver)
@args(conveyor.arg.machine)
@args(conveyor.arg.port)
@args(conveyor.arg.profile)
class ConnectCommand(_MethodCommand):
    name = 'connect'

    help = 'connect to a machine'

    def _create_method_task(self):
        params = {
            'machine_name': self._parsed_args.machine_name,
            'port_name': self._parsed_args.port_name,
            'driver_name': self._get_driver_name(),
            'profile_name': self._get_profile_name(),
            'persistent': True,
        }
        method_task = self._jsonrpc.request('connect', params)
        return method_task

    def _method_callback(self, method_task):
        self._stop_jsonrpc()


@args(conveyor.arg.positional_output_file_optional)
class DefaultConfigCommand(_ClientCommand):
    name = 'defaultconfig'

    help = 'print the platform\'s default conveyor configuration'

    def run(self):
        if None is self._parsed_args.output_file:
            conveyor.config.format_default(sys.stdout)
        else:
            with open(self._parsed_args.output_file, 'w') as fp:
                conveyor.config.format_default(fp)
        return 0


class DirCommand(_JsonCommand):
    name = 'dir'

    help = 'list the methods available from the conveyor service'

    def _create_method_task(self):
        params = {}
        method_task = self._jsonrpc.request('dir', params)
        return method_task

    def _handle_result_default(self, result):
        for method_name, description in result.items():
            lines = textwrap.dedent(description).splitlines()
            def is_blank(s):
                return 0 == len(s) or s.isspace()
            # Remove blank lines at the end of the description. This puts the
            # lines in reverse order.
            lines = list(itertools.dropwhile(is_blank, reversed(lines)))
            # Remove blank lines at the start of the description. This also has
            # the side-effect of putting the lines back in forward order.
            lines = list(itertools.dropwhile(is_blank, reversed(lines)))
            self._log.info('%s:', method_name)
            for line in lines:
                self._log.info('    %s', line)


@args(conveyor.arg.machine)
class DisconnectCommand(_MethodCommand):
    name = 'disconnect'

    help = 'disconnect from a machine'

    def _create_method_task(self):
        params = {
            'machine_name': self._parsed_args.machine_name,
        }
        method_task = self._jsonrpc.request('disconnect', params)
        return method_task

    def _method_callback(self, method_task):
        self._stop_jsonrpc()


@args(conveyor.arg.driver)
@args(conveyor.arg.machine_type)
@args(conveyor.arg.firmware_version)
class DownloadFirmware(_QueryCommand):
    name = 'downloadfirmware'

    help = 'download firmware'

    def _create_method_task(self):
        params = {
            'driver_name': self._get_driver_name(),
            'machine_type': self._parsed_args.machine_type,
            'firmware_version': self._parsed_args.firmware_version,
        }
        method_task = self._jsonrpc.request('downloadfirmware', params)
        return method_task

    def _handle_result(self, result):
        self._log.info('firmware downloaded to: %s', result)


@args(conveyor.arg.positional_driver)
class DriverCommand(_JsonCommand):
    name = 'driver'

    help = 'get the details for a driver'

    def _create_method_task(self):
        params = {'driver_name': self._get_driver_name(),}
        method_task = self._jsonrpc.request('get_driver', params)
        return method_task

    def _handle_result_default(self, result):
        driver = result
        drivers = [driver]
        _print_driver_profiles(self._log, drivers)


class DriversCommand(_JsonCommand):
    name = 'drivers'

    help = 'list the available drivers'

    def _create_method_task(self):
        params = {}
        method_task = self._jsonrpc.request('get_drivers', params)
        return method_task

    def _handle_result_default(self, result):
        drivers = result
        _print_driver_profiles(self._log, drivers)


@args(conveyor.arg.driver)
@args(conveyor.arg.machine_type)
class GetMachineVersions(_QueryCommand):
    name = 'getmachineversions'

    help = 'get the firmware versions available for a machine'

    def _create_method_task(self):
        params = {
            'driver_name': self._get_driver_name(),
            'machine_type': self._parsed_args.machine_type,
        }
        method_task = self._jsonrpc.request('getmachineversions', params)
        return method_task

    def _handle_result(self, result):
        self._log.info('%s', result)


@args(conveyor.arg.driver)
class GetUploadableMachines(_QueryCommand):
    name = 'getuploadablemachines'

    help = 'list the machines to which conveyor can upload firmware'

    def _create_method_task(self):
        params = {'driver_name': self._get_driver_name(),}
        method_task = self._jsonrpc.request('getuploadablemachines', params)
        return method_task

    def _handle_result(self, result):
        print(result)


@args(conveyor.arg.positional_job)
class JobCommand(_JsonCommand):
    name = 'job'

    help = 'get the details for a job'

    def _create_method_task(self):
        params = {'id': int(self._parsed_args.job_id)}
        method_task = self._jsonrpc.request('getjob', params)
        return method_task

    def _handle_result_default(self, result):
        self._log.info('%s', result)


class JobsCommand(_JsonCommand):
    name = 'jobs'

    help = 'get the details for all jobs'

    def _create_method_task(self):
        params = {}
        method_task = self._jsonrpc.request('getjobs', params)
        return method_task

    def _handle_result_default(self, result):
        self._log.info('%s', result)


class PauseCommand(_ConnectedCommand):
    name = 'pause'

    help = 'pause a machine'

    def _create_method_task(self):
        params = {
            'machine_name': self._parsed_args.machine_name,
            'port_name': self._parsed_args.port_name,
            'driver_name': self._get_driver_name(),
            'profile_name': self._get_profile_name(),
        }
        pause_task = self._jsonrpc.request('pause', params)
        return pause_task


class PortsCommand(_JsonCommand):
    name = 'ports'

    help = 'list the available ports'

    def _create_method_task(self):
        params = {}
        method_task = self._jsonrpc.request('getports', params)
        return method_task

    def _handle_result_default(self, result):
        for port in result:
            if conveyor.machine.port.PortType.SERIAL == port['type']:
                self._handle_serial(port)
            else:
                raise ValueError(port['type'])

    def _handle_serial(self, port):
        self._log.info('Serial port:')
        self._log.info('  name    - %s', port['name'])
        self._log.info('  path    - %s', port['path'])
        self._log.info('  iSerial - %s', port['iserial'])
        self._log.info('  VID:PID - %04X:%04X', port['vid'], port['pid'])


@args(conveyor.arg.extruder)
@args(conveyor.arg.gcode_processor)
@args(conveyor.arg.has_start_end)
@args(conveyor.arg.material)
@args(conveyor.arg.slicer)
@args(conveyor.arg.slicer_settings)
@args(conveyor.arg.positional_input_file)
class PrintCommand(_ConnectedCommand):
    name = 'print'

    help = 'print an object'

    def _create_method_task(self):
        slicer_settings = _create_slicer_settings(
            self._parsed_args, self._config)
        slicer_settings.path = self._parsed_args.slicer_settings_path
        extruder_name = _fix_extruder_name(self._parsed_args.extruder_name)
        params = {
            'machine_name': self._machine_name,
            'input_file': os.path.abspath(self._parsed_args.input_file),
            'extruder_name': extruder_name,
            'gcode_processor_names': self._parsed_args.gcode_processor_names,
            'has_start_end': self._parsed_args.has_start_end,
            'material_name': self._parsed_args.material_name,
            'slicer_name': self._parsed_args.slicer_name,
            'slicer_settings': slicer_settings.to_dict(),
        }
        method_task = self._jsonrpc.request('print', params)
        return method_task


@args(conveyor.arg.driver)
@args(conveyor.arg.extruder)
@args(conveyor.arg.gcode_processor)
@args(conveyor.arg.file_type)
@args(conveyor.arg.has_start_end)
@args(conveyor.arg.material)
@args(conveyor.arg.profile)
@args(conveyor.arg.slicer)
@args(conveyor.arg.slicer_settings)
@args(conveyor.arg.positional_input_file)
@args(conveyor.arg.positional_output_file)
class PrintToFileCommand(_MonitorCommand):
    name = 'printtofile'

    help = 'print an object to an .s3g or .x3g file'

    def _create_method_task(self):
        slicer_settings = _create_slicer_settings(
            self._parsed_args, self._config)
        slicer_settings.path = self._parsed_args.slicer_settings_path
        extruder_name = _fix_extruder_name(self._parsed_args.extruder_name)
        params = {
            'driver_name': self._get_driver_name(),
            'profile_name': self._get_profile_name(),
            'input_file': os.path.abspath(self._parsed_args.input_file),
            'output_file': os.path.abspath(self._parsed_args.output_file),
            'extruder_name': extruder_name,
            'file_type': self._parsed_args.file_type,
            'gcode_processor_names': self._parsed_args.gcode_processor_names,
            'has_start_end': self._parsed_args.has_start_end,
            'material_name': self._parsed_args.material_name,
            'slicer_name': self._parsed_args.slicer_name,
            'slicer_settings': slicer_settings.to_dict(),
        }
        method_task = self._jsonrpc.request('print_to_file', params)
        return method_task


class PrintersCommand(_JsonCommand):
    name = 'printers'

    help = 'list connected printers'

    def _create_method_task(self):
        params = {}
        method_task = self._jsonrpc.request('getprinters', params)
        return method_task

    def _handle_result_default(self, result):
        for machine in result:
            self._log.info('Printer:')
            self._log.info('  name        - %s', machine['name'])
            self._log.info('  state       - %s', machine['state'])
            self._log.info('  temperature - %s', machine['temperature'])
            self._log.info('  firmware    - %s', machine['firmware_version'])

            # TODO: stop being lazy and add the rest of the fields.


@args(conveyor.arg.positional_driver)
@args(conveyor.arg.positional_profile)
class ProfileCommand(_JsonCommand):
    name = 'profile'

    help = 'get the details for a profile'

    def _create_method_task(self):
        params = {
            'driver_name': self._get_driver_name(),
            'profile_name': self._get_profile_name(),
        }
        method_task = self._jsonrpc.request('get_profile', params)
        return method_task

    def _handle_result_default(self, result):
        profile = result
        profiles = [profile]
        driver = {
            'name': self._parsed_args.driver_name,
            'profiles': profiles,
        }
        drivers = [driver]
        _print_driver_profiles(self._log, drivers)


@args(conveyor.arg.positional_driver)
class ProfilesCommand(_JsonCommand):
    name = 'profiles'

    help = 'list the available profiles'

    def _create_method_task(self):
        params = {'driver_name': self._get_driver_name(),}
        method_task = self._jsonrpc.request('get_profiles', params)
        return method_task

    def _handle_result_default(self, result):
        profiles = result
        driver = {
            'name': self._parsed_args.driver_name,
            'profiles': profiles,
        }
        drivers = [driver]
        _print_driver_profiles(self._log, drivers)


@args(conveyor.arg.machine)
@args(conveyor.arg.positional_output_file)
class ReadEepromCommand(_QueryCommand):
    name = 'readeeprom'

    help = 'read a machine EEPROM'

    def _create_method_task(self):
        params = {'printername': self._parsed_args.machine_name}
        method_task = self._jsonrpc.request('readeeprom', params)
        return method_task

    def _handle_result(self, result):
        output_file = os.path.abspath(self._parsed_args.output_file)
        with open(output_file, 'w') as fp:
            json.dump(result, fp, sort_keys=True, indent=2)


class ResetToFactoryCommand(_QueryCommand):
    name = 'resettofactory'

    help = 'reset a machine EEPROM to factory settings'

    def _create_method_task(self):
        params = {'printername': None}
        method_task = self._jsonrpc.request('resettofactory', params)
        return method_task

    def _handle_result(self, result):
        pass


@args(conveyor.arg.add_start_end)
@args(conveyor.arg.driver)
@args(conveyor.arg.extruder)
@args(conveyor.arg.gcode_processor)
@args(conveyor.arg.material)
@args(conveyor.arg.profile)
@args(conveyor.arg.slicer)
@args(conveyor.arg.slicer_settings)
@args(conveyor.arg.positional_input_file)
@args(conveyor.arg.positional_output_file)
class SliceCommand(_MonitorCommand):
    name = 'slice'

    help = 'slice an object to a .gcode file'

    def _create_method_task(self):
        slicer_settings = _create_slicer_settings(
            self._parsed_args, self._config)
        slicer_settings.path = self._parsed_args.slicer_settings_path
        extruder_name = _fix_extruder_name(self._parsed_args.extruder_name)
        params = {
            'driver_name': self._get_driver_name(),
            'profile_name': self._get_profile_name(),
            'input_file': os.path.abspath(self._parsed_args.input_file),
            'output_file': os.path.abspath(self._parsed_args.output_file),
            'add_start_end': self._parsed_args.add_start_end,
            'extruder_name': extruder_name,
            'gcode_processor_names': self._parsed_args.gcode_processor_names,
            'material_name': self._parsed_args.material_name,
            'slicer_name': self._parsed_args.slicer_name,
            'slicer_settings': slicer_settings.to_dict(),
        }
        method_task = self._jsonrpc.request('slice', params)
        return method_task


class UnpauseCommand(_ConnectedCommand):
    name = 'unpause'

    help = 'unpause a machine'

    def _create_method_task(self):
        params = {
            'machine_name': self._parsed_args.machine_name,
            'port_name': self._parsed_args.port_name,
            'driver_name': self._get_driver_name(),
            'profile_name': self._get_profile_name(),
        }
        pause_task = self._jsonrpc.request('unpause', params)
        return pause_task


@args(conveyor.arg.machine_type)
@args(conveyor.arg.positional_input_file)
class UploadFirmwareCommand(_QueryCommand):
    name = 'uploadfirmware'

    help = 'upload firmware'

    def _create_method_task(self):
        params = {
            'machine_name': None,
            'machinetype': self._parsed_args.machine_type,
            'filename': os.path.abspath(self._parsed_args.input_file),
        }
        method_task = self._jsonrpc.request('uploadfirmware', params)
        return method_task

    def _handle_result(self, result):
        pass


@args(conveyor.arg.positional_input_file)
class VerifyS3gCommand(_QueryCommand):
    name = 'verifys3g'

    help = 'verify an s3g/x3g file.'

    def _create_method_task(self):
        params = {'s3gpath': os.path.abspath(self._parsed_args.input_file)}
        method_task = self._jsonrpc.request('verifys3g', params)
        return method_task

    def _handle_result(self, result):
        print('Your s3g file is %s valid' % ('NOT' if result is False else '',))


class WaitForServiceCommand(_ClientCommand):
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


@args(conveyor.arg.positional_input_file)
class WriteEepromCommand(_QueryCommand):
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


def _fix_extruder_name(extruder_name):
    if 'right' == extruder_name:
        result = '0'
    elif 'left' == extruder_name:
        result = '1'
    elif 'both' == extruder_name:
        result = '0,1'
    else:
        raise ValueError(extruder_name)
    return result


def _create_slicer_settings(parsed_args, config):
    if 'miraclegrue' == parsed_args.slicer_name:
        slicer = conveyor.slicer.Slicer.MIRACLEGRUE
    elif 'skeinforge' == parsed_args.slicer_name:
        slicer = conveyor.slicer.Slicer.SKEINFORGE
    else:
        raise ValueError(parsed_args.slicer_name)
    extruder_name = _fix_extruder_name(parsed_args.extruder_name)
    slicer_settings = conveyor.domain.SlicerConfiguration(
        slicer=slicer,
        extruder=extruder_name,
        raft=bool(
            config.get('client', 'slicing', 'raft')),
        support=bool(
            config.get('client', 'slicing', 'support')),
        infill=float(
            config.get('client', 'slicing', 'infill')),
        layer_height=float(
            config.get('client', 'slicing', 'layer_height')),
        shells=int(
            config.get('client', 'slicing', 'shells')),
        extruder_temperature=float(
            config.get('client', 'slicing', 'extruder_temperature')),
        platform_temperature=float(
            config.get('client', 'slicing', 'platform_temperature')),
        print_speed=float(
            config.get('client', 'slicing', 'print_speed')),
        travel_speed=float(
            config.get('client', 'slicing', 'travel_speed')),
    )
    return slicer_settings


def _print_driver_profiles(log, drivers):
    log.info('drivers:')
    for driver in drivers:
        log.info('  %s:', driver['name'])
        for profile in driver['profiles']:
            log.info('    %s:', profile['name'])
            log.info('      X axis size       - %s', profile['xsize'])
            log.info('      Y axis size       - %s', profile['ysize'])
            log.info('      Z axis size       - %s', profile['zsize'])
            log.info('      can print         - %s', profile['can_print'])
            log.info('      can print to file - %s', profile['can_print_to_file'])
            log.info('      heated platform   - %s', profile['has_heated_platform'])
            log.info('      number of tools   - %d', profile['number_of_tools'])
