# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/server/__init__.py
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

import collections
import logging
import os.path
import threading

import conveyor.connection
import conveyor.job
import conveyor.jsonrpc
import conveyor.log
import conveyor.recipe
import conveyor.slicer
import conveyor.slicer.miraclegrue
import conveyor.slicer.skeinforge
import conveyor.stoppable
import conveyor.util

from conveyor.decorator import jsonrpc


class Server(conveyor.stoppable.StoppableInterface):
    def __init__(
            self, config, driver_manager, port_manager, machine_manager,
            spool, connection_manager, listener):
        conveyor.stoppable.StoppableInterface.__init__(self)
        self._config = config
        self._driver_manager = driver_manager
        self._port_manager = port_manager
        self._machine_manager = machine_manager
        self._spool = spool
        self._connection_manager = connection_manager
        self._listener = listener
        self._stop = False
        self._log = conveyor.log.getlogger(self)
        self._clients = set()
        self._clients_condition = threading.Condition()
        self._queue = collections.deque()
        self._queue_condition = threading.Condition()
        self._job_id_counter = 0
        self._jobs = {}
        self._jobs_condition = threading.Condition()
        self._print_queued = set()
        self._print_queued_condition = threading.Condition()
        self._port_manager.port_attached.attach(self._port_attached)
        self._port_manager.port_detached.attach(self._port_detached)

    def stop(self):
        self._stop = True
        with self._queue_condition:
            self._queue_condition.notify_all()

    def run(self):
        work_thread = threading.Thread(target=self._work_queue_target)
        work_thread.start()
        try:
            while not self._stop:
                connection = self._listener.accept()
                if None is not connection:
                    jsonrpc = conveyor.jsonrpc.JsonRpc(connection, connection)
                    client = _Client(self._config, self, jsonrpc)
                    client.start()
        finally:
            work_thread.join(1)
        return 0

    def queue_work(self, work):
        with self._queue_condition:
            self._queue.appendleft(work)
            self._queue_condition.notify_all()

    def _work_queue_target(self):
        while not self._stop:
            def func():
                with self._queue_condition:
                    if 0 == len(self._queue):
                        self._queue_condition.wait()
                    if 0 == len(self._queue):
                        work = None
                    else:
                        work = self._queue.pop()
                if None is not work:
                    work()
            conveyor.error.guard(self._log, func)

    def _port_attached(self, port):
        with self._clients_condition:
            clients = self._clients.copy()
        port_info = port.get_info()
        _Client.port_attached(clients, port_info)

    def _port_detached(self, port_name):
        with self._clients_condition:
            clients = self._clients.copy()
        _Client.port_detached(clients, port_name)

    def _machine_connected(self, machine):
        pass # TODO

    def _machine_state_changed(self, machine):
        with self._clients_condition:
            clients = self._clients.copy()
        machine_info = machine.get_info()
        _Client.machine_state_changed(clients, machine_info)

    def _machine_temperature_changed(self, machine):
        with self._clients_condition:
            clients = self._clients.copy()
        machine_info = machine.get_info()
        _Client.machine_temperature_changed(clients, machine_info)

    def _add_client(self, client):
        with self._clients_condition:
            self._clients.add(client)

    def _get_clients(self):
        with self._clients_condition:
            clients = self._clients.copy()
        return clients

    def _remove_client(self, client):
        with self._clients_condition:
            self._clients.remove(client)

    def _add_job(self, job):
        with self._jobs_condition:
            self._jobs[job.id] = job
        with self._clients_condition:
            clients = self._clients.copy()
        job_info = job.get_info()
        _Client.job_added(clients, job_info)

    def _job_changed(self, job):
        job_info = job.get_info()
        with self._clients_condition:
            clients = self._clients.copy()
        _Client.job_changed(clients, job_info)

    def _find_port_by_port_name(self, port_name):
        if None is not port_name:
            port = self._port_manager.get_port(port_name)
        else:
            ports = self._port_manager.get_ports()
            if 0 == len(ports):
                raise conveyor.error.NoPortsException
            elif len(ports) > 1:
                raise conveyor.error.MultiplePortsException
            else:
                port = ports[0]
        return port

    def _find_port_by_machine_name(self, machine_name):
        for port in self._port_manager.get_ports():
            if port.has_machine_name(machine_name):
                return port
        else:
            raise conveyor.error.UnknownMachineError(machine_name)

    def _find_driver(self, port, driver_name):
        if None is not driver_name:
            driver = self._driver_manager.get_driver(driver_name)
        elif 0 == len(port.driver_profiles):
            raise conveyor.error.NoDriversException
        elif len(port.driver_profiles) > 1:
            raise MultipleDriversException
        else:
            # NOTE: this loop extracts the single driver.
            for driver_name in port.driver_profiles.keys():
                driver = self._driver_manager.get_driver(driver_name)
        return driver

    def _find_profile(self, port, driver, profile_name):
        if None is not profile_name:
            profile = driver.get_profile(profile_name)
        else:
            profiles = port.driver_profiles[driver.name]
            if 1 == len(profiles):
                profile = profiles[0]
            else:
                # NOTE: when there are no profiles or multiple profiles, we set
                # `profile` to `None` and expect that the driver determines the
                # correct profile. It will raise an exception if it cannot.
                profile = None
        return profile

    # TODO: this `_find_machine` business is complicated. There's probably some
    # opportunity for refactoring and condensing this, but for now I'm going to
    # leave it alone for fear of breaking something.
    #
    # Also, the current logic doesn't cover every possible case. For example,
    # you could pass only `driver_name` and it *should* (but does not) winnow
    # the list of ports down to those that support that driver. This would mean
    # restructuring the lookup as a series of filter stages.

    def _find_machine(
            self, machine_name, port_name, driver_name, profile_name):
        if None is not machine_name:
            try:
                machine = self._machine_manager.get_machine(machine_name)
            except conveyor.error.UnknownMachineError:
                port = self._find_port_by_machine_name(machine_name)
                driver = self._find_driver(port, driver_name)
                profile = self._find_profile(port, driver, profile_name)
                machine = self._machine_manager.new_machine(
                    port, driver, profile)
                machine.state_changed.attach(self._machine_state_changed)
                machine.temperature_changed.attach(
                    self._machine_temperature_changed)
            else:
                if None is port_name:
                    port = self._find_port_by_machine_name(machine_name)
                    machine.set_port(port)
                    port.set_machine(machine)
                else:
                    port = self._port_manager.get_port(port_name)
                    machine_port = machine.get_port()
                    if None is machine_port:
                        machine.set_port(port)
                        port.set_machine(machine)
                    elif machine_port.name != port.name:
                        raise conveyor.error.PortMismatchException
                driver = machine.get_driver()
                if None is not driver_name and driver_name != driver.name:
                    raise conveyor.error.DriverMismatchException
                else:
                    profile = machine.get_profile()
                    if None is not profile_name and profile_name != profile.name:
                        raise conveyor.error.ProfileMismatchException
        else:
            port = self._find_port_by_port_name(port_name)
            driver = self._find_driver(port, driver_name)
            profile = self._find_profile(port, driver, profile_name)
            machine_name = port.get_machine_name()
            if None is machine_name:
                raise conveyor.error.MissingMachineNameException
            else:
                try:
                    machine = self._machine_manager.get_machine(machine_name)
                except conveyor.error.UnknownMachineError:
                    machine = self._machine_manager.new_machine(
                        port, driver, profile)
                    machine.state_changed.attach(self._machine_state_changed)
                    machine.temperature_changed.attach(
                        self._machine_temperature_changed)
                else:
                    machine.set_port(port)
                    port.set_machine(machine)
        return machine

    def get_ports(self):
        ports = self._port_manager.get_ports()
        return ports

    def get_drivers(self):
        drivers = self._driver_manager.get_drivers()
        return drivers

    def get_driver(self, driver_name):
        driver = self._driver_manager.get_driver(driver_name)
        return driver

    def get_profiles(self, driver_name):
        driver = self._driver_manager.get_driver(driver_name)
        profiles = driver.get_profiles(None)
        return profiles

    def get_profile(self, driver_name, profile_name):
        driver = self._driver_manager.get_driver(driver_name)
        profile = driver.get_profile(profile_name)
        return profile

    def get_machines(self):
        machines = self._machine_manager.get_machines()
        return machines

    def connect(
            self, client, machine_name, port_name, driver_name, profile_name,
            persistent):
        machine = self._find_machine(
            machine_name, port_name, driver_name, profile_name)
        if conveyor.machine.MachineState.DISCONNECTED == machine.get_state():
            machine.connect()
            self._machine_connected(machine)
        self._connection_manager.acquire_machine(client, machine, persistent)
        return machine

    def disconnect(self, machine_name):
        machine = self._find_machine(machine_name, None, None, None)
        machine.disconnect()

    def print(
            self, machine_name, input_file, extruder_name,
            gcode_processor_names, has_start_end, material_name, slicer_name,
            slicer_settings):
        job_id = self._create_job_id()
        job_name = self._get_job_name(input_file)
        machine = self._find_machine(machine_name, None, None, None)
        if self._is_print_queued(machine) or not machine.is_idle():
            raise conveyor.error.PrintQueuedException
        else:
            job = conveyor.job.PrintJob(
                job_id, job_name, machine, input_file, extruder_name,
                gcode_processor_names, has_start_end, material_name, slicer_name,
                slicer_settings)
            recipe_manager = conveyor.recipe.RecipeManager(
                self._config, self, self._spool)
            job.task = conveyor.task.Task()
            self._attach_print_queued_callbacks(machine, job.task)
            self._attach_job_callbacks(job)
            recipe_manager.cook(job)
            job.task.start()
            return job

    def pause(self, machine_name):
        machine = self._find_machine(machine_name, None, None, None)
        machine.pause()

    def unpause(self, machine_name):
        machine = self._find_machine(machine_name, None, None, None)
        machine.unpause()

    def print_to_file(
            self, driver_name, profile_name, input_file, output_file,
            extruder_name, file_type, gcode_processor_names, has_start_end,
            material_name, slicer_name, slicer_settings):
        job_id = self._create_job_id()
        job_name = self._get_job_name(output_file)
        driver = self._driver_manager.get_driver(driver_name)
        profile = driver.get_profile(profile_name)
        job = conveyor.job.PrintToFileJob(
            job_id, job_name, driver, profile, input_file, output_file,
            extruder_name, file_type, gcode_processor_names, has_start_end,
            material_name, slicer_name, slicer_settings)
        recipe_manager = conveyor.recipe.RecipeManager(
            self._config, self, self._spool)
        job.task = conveyor.task.Task()
        self._attach_job_callbacks(job)
        recipe_manager.cook(job)
        job.task.start()
        return job

    def slice(
            self, driver_name, profile_name, input_file, output_file,
            add_start_end, extruder_name, gcode_processor_names, material_name,
            slicer_name, slicer_settings):
        job_id = self._create_job_id()
        job_name = self._get_job_name(output_file)
        driver = self._driver_manager.get_driver(driver_name)
        profile = driver.get_profile(profile_name)
        job = conveyor.job.SliceJob(
            job_id, job_name, driver, profile, input_file, output_file,
            add_start_end, extruder_name, gcode_processor_names,
            material_name, slicer_name, slicer_settings)
        recipe_manager = conveyor.recipe.RecipeManager(
            self._config, self, self._spool)
        job.task = conveyor.task.Task()
        self._attach_job_callbacks(job)
        recipe_manager.cook(job)
        job.task.start()
        return job

    def get_jobs(self, client):
        with self._jobs_condition:
            jobs = self._jobs.copy()
        return jobs

    def get_job(self, job_id):
        with self._jobs_condition:
            try:
                job = self._jobs[job_id]
            except KeyError:
                raise conveyor.error.UnknownJobError(job_id)
            else:
                return job

    def cancel_job(self, job_id):
        job = self.get_job(job_id)
        if conveyor.task.TaskState.STOPPED != job.task.state:
            job.task.cancel()

    def _create_job_id(self):
        with self._jobs_condition:
            self._job_id_counter += 1
            id_ = self._job_id_counter
        return id_

    def _get_job_name(self, p):
        root, ext = os.path.splitext(p)
        job_name = os.path.basename(root)
        return job_name

    def _attach_job_callbacks(self, job):
        def start_callback(task):
            job.log_job_started(self._log)
            self._add_job(job)
        job.task.startevent.attach(start_callback)
        def heartbeat_callback(task):
            job.log_job_heartbeat(self._log)
            self._job_changed(job)
        job.task.heartbeatevent.attach(heartbeat_callback)
        def stopped_callback(task):
            job.log_job_stopped(self._log)
            self._job_changed(job)
        job.task.stoppedevent.attach(stopped_callback)

    def _attach_print_queued_callbacks(self, machine, task):
        def start_callback(task):
            self._add_print_queued(machine)
        task.startevent.attach(start_callback)
        def stopped_callback(task):
            self._remove_print_queued(machine)
        task.stoppedevent.attach(stopped_callback)

    def _add_print_queued(self, machine):
        with self._print_queued_condition:
            self._print_queued.add(machine.name)

    def _remove_print_queued(self, machine):
        with self._print_queued_condition:
            self._print_queued.remove(machine.name)

    def _is_print_queued(self, machine):
        with self._print_queued_condition:
            result = machine.name in self._print_queued
        return result

    ## old stuff ##############################################################

    def get_uploadable_machines(self, driver_name):
        driver = self._driver_manager.get_driver(driver_name)
        task = conveyor.task.Task()
        driver.get_uploadable_machines(task)
        return task

    def get_machine_versions(self, driver_name, machine_type):
        driver = self._driver_manager.get_driver(driver_name)
        task = conveyor.task.Task()
        driver.get_machine_versions(machine_type, task)
        return task

    def compatible_firmware(self, driver_name, firmware_version):
        driver = self._driver_manager.get_driver(driver_name)
        result = driver.compatible_firmware(firmware_version)
        return result

    def download_firmware(self, driver_name, machine_type, firmware_version):
        driver = self._driver_manager.get_driver(driver_name)
        task = conveyor.task.Task()
        driver.download_firmware(machine_type, firmware_version, task)
        return task

    def verify_s3g(self, input_file):
        task = conveyor.recipe.Recipe.verifys3gtask(s3gpath)
        return task

    def reset_to_factory(self, machine_name):
        machine = self._find_machine(machine_name, None, None, None)
        task = conveyor.task.Task()
        machine.reset_to_factory(task)
        return task

    def upload_firmware(self, machine_name, machine_type, input_file):
        machine = self._find_machine(machine_name, None, None, None)
        task = conveyor.task.Task()
        machine.upload_firmware(machine_type, input_file, task)
        return task

    def read_eeprom(self, machine_name):
        machine = self._find_machine(machine_name, None, None, None)
        task = conveyor.task.Task()
        machine.read_eeprom(task)
        return task

    def write_eeprom(self, machine_name, eeprom_map):
        machine = self._find_machine(machine_name, None, None, None)
        task = conveyor.task.Task()
        machine.write_eeprom(eeprom_map, task)
        return task


class _Client(conveyor.stoppable.StoppableThread):
    '''
    This is the `Server`'s notion of a client. One `_Client` is allocated for
    each incoming connection.

    '''

    def __init__(self, config, server, jsonrpc):
        conveyor.stoppable.StoppableThread.__init__(self)
        self._config = config
        self._server = server
        self._jsonrpc = jsonrpc
        self._log = conveyor.log.getlogger(self)

    def stop(self):
        self._jsonrpc.stop()

    def run(self):
        def func():
            conveyor.jsonrpc.install(self._jsonrpc, self)
            self._server._add_client(self)
            try:
                self._jsonrpc.run()
            finally:
                self._server._remove_client(self)
        conveyor.error.guard(self._log, func)

    @staticmethod
    def port_attached(clients, port_info):
        params = port_info.to_dict()
        for client in clients:
            client._jsonrpc.notify('port_attached', params)

    @staticmethod
    def port_detached(clients, port_name):
        params = {'port_name': port_name}
        for client in clients:
            client._jsonrpc.notify('port_detached', params)

    @staticmethod
    def machine_state_changed(clients, machine_info):
        params = machine_info.to_dict()
        for client in clients:
            client._jsonrpc.notify('machine_state_changed', params)

    @staticmethod
    def machine_temperature_changed(clients, machine_info):
        params = machine_info.to_dict()
        for client in clients:
            client._jsonrpc.notify('machine_temperature_changed', params)

    @staticmethod
    def job_added(clients, job_info):
        params = job_info.to_dict()
        for client in clients:
            client._jsonrpc.notify('jobadded', params)

    @staticmethod
    def job_changed(clients, job_info):
        params = job_info.to_dict()
        for client in clients:
            client._jsonrpc.notify('jobchanged', params)

    @jsonrpc()
    def hello(self):
        '''
        This is the first method any client must invoke after connecting to the
        conveyor service.

        '''
        return 'world'

    @jsonrpc()
    def dir(self):
        '''
        Lists the methods available from the conveyor service.

        '''
        result = {}
        methods = self._jsonrpc.getmethods()
        result = {}
        for k, f in methods.items():
            doc = getattr(f, '__doc__', None)
            if None is not doc:
                result[k] = f.__doc__
        result['__version__'] = conveyor.__version__
        return result

    @jsonrpc()
    def getports(self):
        result = []
        for port in self._server.get_ports():
            dct = port.get_info().to_dict()
            result.append(dct)
        return result

    @jsonrpc()
    def get_drivers(self):
        result = []
        for driver in self._server.get_drivers():
            dct = driver.get_info().to_dict()
            result.append(dct)
        return result

    @jsonrpc()
    def get_driver(self, driver_name):
        driver = self._server.get_driver(driver_name)
        result = driver.get_info().to_dict()
        return result

    @jsonrpc()
    def get_profiles(self, driver_name):
        result = []
        for profile in self._server.get_profiles(driver_name):
            dct = profile.get_info().to_dict()
            result.append(dct)
        return result

    @jsonrpc()
    def get_profile(self, driver_name, profile_name):
        profile = self._server.get_profile(driver_name, profile_name)
        result = profile.get_info().to_dict()
        return result

    @jsonrpc()
    def connect(
            self, machine_name, port_name, driver_name, profile_name,
            persistent):
        machine = self._server.connect(
            self, machine_name, port_name, driver_name, profile_name,
            persistent)
        dct = machine.get_info().to_dict()
        return dct

    @jsonrpc()
    def disconnect(self, machine_name):
        self._server.disconnect(machine_name)
        return None

    @jsonrpc()
    def print(
            self, machine_name, input_file, extruder_name,
            gcode_processor_names, has_start_end, material_name, slicer_name,
            slicer_settings):
        slicer_settings = conveyor.domain.SlicerConfiguration.fromdict(
            slicer_settings)
        job = self._server.print(
            machine_name, input_file, extruder_name,
            gcode_processor_names, has_start_end, material_name, slicer_name,
            slicer_settings)
        dct = job.get_info().to_dict()
        return dct

    @jsonrpc()
    def pause(self, machine_name):
        self._server.pause(machine_name)
        return None

    @jsonrpc()
    def unpause(self, machine_name):
        self._server.unpause(machine_name)
        return None

    @jsonrpc()
    def getprinters(self):
        result = []
        for machine in self._server.get_machines():
            dct = machine.get_info().to_dict()
            result.append(dct)
        # TODO: this is horrible... it is coupled to the s3g driver.
        for driver in self._server._driver_manager.get_drivers():
            for profile in driver.get_profiles(None):
                info = conveyor.machine.MachineInfo(
                    profile._s3g_profile.values['type'], None, driver.name,
                    profile.name, conveyor.machine.MachineState.DISCONNECTED)
                info.display_name = profile._s3g_profile.values['type']
                info.unique_name = profile._s3g_profile.values['type']
                info.printer_type = profile._s3g_profile.values['type']
                info.machine_names = profile._s3g_profile.values['machinenames']
                info.can_print = False
                info.can_print_to_file = True
                info.has_heated_platform = (0 != len(profile._s3g_profile.values['heated_platforms']))
                info.number_of_toolheads = len(profile._s3g_profile.values['tools'])
                axes = profile._s3g_profile.values['axes']
                info.build_volume = [axes['X']['platform_length'],
                                     axes['Y']['platform_length'],
                                     axes['Z']['platform_length']]
                info.temperature = {'tools': {}, 'heated_platforms': {},}
                info.firmware_version = None
                dct = info.to_dict()
                result.append(dct)
        return result

    @jsonrpc()
    def print_to_file(
            self, driver_name, profile_name, input_file, output_file,
            extruder_name, file_type, gcode_processor_names, has_start_end,
            material_name, slicer_name, slicer_settings):
        slicer_settings = conveyor.domain.SlicerConfiguration.fromdict(
            slicer_settings)
        job = self._server.print_to_file(
            driver_name, profile_name, input_file, output_file,
            extruder_name, file_type, gcode_processor_names, has_start_end,
            material_name, slicer_name, slicer_settings)
        dct = job.get_info().to_dict()
        return dct

    @jsonrpc()
    def slice(
            self, driver_name, profile_name, input_file, output_file,
            add_start_end, extruder_name, gcode_processor_names,
            material_name, slicer_name, slicer_settings):
        slicer_settings = conveyor.domain.SlicerConfiguration.fromdict(
            slicer_settings)
        job = self._server.slice(
            driver_name, profile_name, input_file, output_file, add_start_end,
            extruder_name, gcode_processor_names, material_name, slicer_name,
            slicer_settings)
        dct = job.get_info().to_dict()
        return dct

    @jsonrpc()
    def getjobs(self):
        jobs = self._server.get_jobs(self)
        result = {}
        for job_id in jobs:
            result[job_id] = jobs[job_id].get_info().to_dict()
        return result

    @jsonrpc()
    def getjob(self, id):
        job = self._server.get_job(id)
        result = job.to_dict()
        return result

    @jsonrpc()
    def canceljob(self, id):
        self._server.cancel_job(id)
        return None

    @jsonrpc()
    def getuploadablemachines(self, driver_name):
        task = self._server.get_uploadable_machines(driver_name)
        return task

    @jsonrpc()
    def getmachineversions(self, driver_name, machine_type):
        task = self._server.get_machine_versions(driver_name, machine_type)
        return task

    @jsonrpc()
    def compatiblefirmware(self, driver_name, firmware_version):
        result = self._server.compatible_firmware(self, firmware_version)
        return result

    @jsonrpc()
    def downloadfirmware(self, driver_name, machine_type, firmware_version):
        task = self._server.download_firmware(
            driver_name, machine_type, firmware_version)
        return task

    @jsonrpc()
    def verifys3g(self, s3gpath):
        task = self._server.verify_s3g(s3gpath)
        return task

    @jsonrpc()
    def resettofactory(self, machine_name):
        task = self._server.reset_to_factory(machine_name)
        return task

    @jsonrpc()
    def uploadfirmware(self, machine_name, machinetype, filename):
        task = self._server.upload_firmware(
            machine_name, machinetype, filename)
        return task

    @jsonrpc()
    def readeeprom(self, printername):
        task = self._server.read_eeprom(printername)
        return task

    @jsonrpc()
    def writeeeprom(self, printername, eeprommap):
        task = self._server.write_eeprom(printername, eeprommap)
        return task


class ConnectionManager(object):
    def __init__(self, machine_manager, spool):
        self._machine_manager = machine_manager
        self._spool = spool
        self._acquired_machines = collections.defaultdict(set)
        self._acquired_machines_condition = threading.Condition()

    def acquire_machine(self, client, machine, persistent):
        pass

    def client_removed(self):
        pass

    def job_changed(self, job):
        pass
