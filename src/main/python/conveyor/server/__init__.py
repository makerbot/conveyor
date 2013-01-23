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
import makerbot_driver
import os.path
import threading
import urllib2

import conveyor.connection
import conveyor.job
import conveyor.jsonrpc
import conveyor.recipe
import conveyor.slicer.miraclegrue
import conveyor.slicer.skeinforge
import conveyor.stoppable
import conveyor.util

from conveyor.decorator import jsonrpc


class _ClientThread(conveyor.stoppable.StoppableThread):
    @classmethod
    def create(cls, config, server, connection, id):
        jsonrpc = conveyor.jsonrpc.JsonRpc(connection, connection)
        clientthread = _ClientThread(config, server, jsonrpc, id)
        return clientthread

    def __init__(self, config, server, jsonrpc, id):
        conveyor.stoppable.StoppableThread.__init__(self)
        self._config = config
        self._log = logging.getLogger(self.__class__.__name__)
        self._server = server
        self._id = id
        self._jsonrpc = jsonrpc
        self._printers_seen = []

    def printeradded(self, params):
        self._jsonrpc.notify('printeradded', params)

    def printerchanged(self, params):
        self._jsonrpc.notify('printerchanged', params)

    def printerremoved(self, params):
        self._jsonrpc.notify('printerremoved', params)

    def jobadded(self, params):
        self._jsonrpc.notify('jobadded', params)

    def jobchanged(self, params):
        self._jsonrpc.notify('jobchanged', params)

    def _stoppedcallback(self, job):
        def callback(task):
            job.state = task.state
            job.conclusion = task.conclusion
            job.failure = None
            if None is not task.failure:
                if isinstance(task.failure.failure, dict):
                    job.failure = task.failure.failure
                else:
                    job.failure = unicode(task.failure.failure)
            if conveyor.task.TaskConclusion.ENDED == task.conclusion:
                self._log.info('job %d ended', job.id)
            elif conveyor.task.TaskConclusion.FAILED == task.conclusion:
                self._log.info('job %d failed: %s', job.id, job.failure)
            elif conveyor.task.TaskConclusion.CANCELED == task.conclusion:
                self._log.info('job %d canceled', job.id)
            else:
                raise ValueError(task.conclusion)
            self._server.changejob(job)
        return callback

    @jsonrpc('hello')
    def _hello(self):
        '''
        This is the first method any client must invoke after connecting to the
        conveyor service.

        '''
        return 'world'

    @jsonrpc('dir')
    def _dir(self):
        '''
        Lists the methods available from the conveyor service.

        '''

        self._log.debug('')
        result = {}
        methods = self._jsonrpc.getmethods()
        result = {}
        for k, f in methods.items():
            doc = getattr(f, '__doc__', None)
            if None is not doc:
                result[k] = f.__doc__
        result['__version__'] = conveyor.__version__
        return result

    def _findprinter(self, name):
        printerthread = None
        if None is name:
            printerthread = self._findprinter_default()
            if None is printerthread:
                raise Exception('no printer connected') # TODO: custom exception
        else:
            printerthread = self._server.findprinter_printerid(name)
            if None is printerthread:
                printerthread = self._server.findprinter_portname(name)
            if None is printerthread:
                raise Exception('unknown printer: %s' % (name,)) # TODO: custom exception
        return printerthread

    def _findprinter_default(self):
        printerthreads = self._server.getprinterthreads()
        keys = printerthreads.keys()
        if 0 == len(keys):
            printerthread = None
        else:
            key = keys[0]
            printerthread = self._server._printerthreads[key]
        return printerthread

    def _findprofile(self, name):
        profile = makerbot_driver.Profile(name, self._config.get(
            'makerbot_driver', 'profile_dir'))
        return profile

    def _getbuildname(self, path):
        root, ext = os.path.splitext(path)
        buildname = os.path.basename(root)
        return buildname

    @jsonrpc('print')
    def _print(
            self, machine_name, port_name, driver_name, profile_name,
            input_file, extruder_name, gcode_processor_name, has_start_end,
            material_name, slicer_name, slicer_settings):
        id = self._create_job_id()
        name = self._get_job_name(input_file)
        job = conveyor.job.PrintJob(
            id, name, machine_name, port_name, driver_name, profile_name,
            input_file, extruder_name, gcode_processor_name,
            has_start_end, material_name, slicer_name, slicer_settings)
        # TODO: create process and start job
        return job

    @jsonrpc('print_to_file')
    def _print_to_file(
            self, driver_name, profile_name, input_file, output_file,
            extruder_name, file_type, gcode_processor_name, has_start_end,
            material_name, slicer_name, slicer_settings):
        id = self._create_job_id()
        name = self._get_job_name(input_file)
        job = conveyor.job.PrintToFileJob(
            id, name, driver_name, profile_name, input_file, output_file,
            extruder_name, gcode_processor_name, has_start_end,
            material_name, slicer_name, slicer_settings)
        # TODO: create process and start job
        return job

    @jsonrpc('slice')
    def _slice(
            self, driver_name, profile_name, input_file, output_file,
            add_start_end, extruder_name, gcode_processor_name,
            material_name, slicer_name, slicer_settings):
        id = self._create_job_id()
        name = conveyor.job.SliceJob(
            id, name, driver_name, profile_name, input_file,
            output_file, add_start_end, extruder_name, gcode_processor_name,
            material_name, slicer_name, slicer_settings)
        # TODO: create process and start job
        return job

    @jsonrpc('canceljob')
    def _canceljob(self, id):
        self._server.canceljob(id)

    @jsonrpc('getprinters')
    def _getprinters(self):
        result = []
        profiledir = self._config.get('makerbot_driver', 'profile_dir')
        profile_names = list(makerbot_driver.list_profiles(profiledir))
        for profile_name in profile_names:
            if 'recipes' != profile_name:
                profile = makerbot_driver.Profile(profile_name, profiledir)
                printer = conveyor.domain.Printer.fromprofile(
                    profile, profile_name, None, None)
                printer.can_print = False
                dct = printer.todict()
                result.append(dct)
        printerthreads = self._server.getprinterthreads()
        for portname, printerthread in printerthreads.items():
            profile = printerthread.getprofile()
            printerid = printerthread.getprinterid()
            firmware_version = printerthread.get_firmware_version()
            printer = conveyor.domain.Printer.fromprofile(
                profile, printerid, None, firmware_version)
            dct = printer.todict()
            result.append(dct)
        return result

    @jsonrpc('getjobs')
    def _getjobs(self):
        jobs = self._server.getjobs()
        result = {}
        for job in jobs.values():
            dct = job.todict()
            result[job.id] = dct
        return result

    @jsonrpc('getjob')
    def _getjob(self, id):
        job = self._server.getjob(id)
        result = job.todict()
        return result

    @jsonrpc('resettofactory')
    def _resettofactory(self, printername):
        printerthread = self._findprinter(printername)
        task = conveyor.task.Task()
        printerthread.resettofactory(task)

    @jsonrpc('getuploadablemachines')
    def _getuploadablemachines(self):
        task = conveyor.task.Task()
        def runningcallback(task):
            try:
                uploader = makerbot_driver.Firmware.Uploader()
                machines = uploader.list_machines()
                task.end(machines)
            except Exception as e:
                message = unicode(e)
                task.fail(message)
        task.runningevent.attach(runningcallback)
        return task

    @jsonrpc('getmachineversions')
    def _getmachineversions(self, machine_type):
        task = conveyor.task.Task()
        def runningcallback(task):
            try:
                uploader = makerbot_driver.Firmware.Uploader()
                versions = uploader.list_firmware_versions(machine_type)
                task.end(versions)
            except Exception as e:
                message = unicode(e)
                task.fail(message)
        task.runningevent.attach(runningcallback)
        return task

    @jsonrpc('compatiblefirmware')
    def _compatiblefirmware(self, firmwareversion):
        uploader = makerbot_driver.Firmware.Uploader(autoUpdate=False)
        return uploader.compatible_firmware(firmwareversion)

    @jsonrpc('downloadfirmware')
    def _downloadfirmware(self, machinetype, version):
        task = conveyor.task.Task()
        def runningcallback(task):
            try:
                uploader = makerbot_driver.Firmware.Uploader()
                hex_file_path = uploader.download_firmware(machinetype, version)
                task.end(hex_file_path)
            except Exception as e:
                message = unicode(e)
                task.fail(message)
        task.runningevent.attach(runningcallback)
        return task

    @jsonrpc('uploadfirmware')
    def _uploadfirmware(self, printername, machinetype, filename):
        task = conveyor.task.Task()
        def runningcallback(task):
            try:
                printerthread = self._findprinter(printername)
                printerthread.uploadfirmware(machinetype, filename, task)
            except Exception as e:
                self._log.debug('handled exception')
                message = unicode(e)
                task.fail(message)
            else:
                task.end(None)
        task.runningevent.attach(runningcallback)
        return task

    @jsonrpc('readeeprom')
    def _readeeprom(self, printername):
        task = conveyor.task.Task()
        def runningcallback(task):
            try:
                printerthread = self._findprinter(printername)
                eeprommap = printerthread.readeeprom(task)
            except Exception as e:
                self._log.debug('handled exception')
                failure = conveyor.util.exception_to_failure(e)
                tail.fail(failure)
            else:
                task.end(eeprommap)
        task.runningevent.attach(runningcallback)
        return task

    @jsonrpc('writeeeprom')
    def _writeeeprom(self, printername, eeprommap):
        task = conveyor.task.Task()
        def runningcallback(task):
            try:
                printerthread = self._findprinter(printername)
                printerthread.writeeeprom(eeprommap, task)
            except Exception as e:
                self._log.debug('handled exception')
                failure = conveyor.util.exception_to_failure(e)
                tail.fail(failure)
            else:
                task.end(None)
        task.runningevent.attach(runningcallback)
        return task

    @jsonrpc('verifys3g')
    def _verifys3g(self, s3gpath):
        task = conveyor.recipe.Recipe.verifys3gtask(s3gpath)
        return task

    @jsonrpc('getports')
    def _getports(self):
        result = []
        for port in self._server._port_manager.get_ports():
            result.append(port.to_dict())
        return result

    @jsonrpc('connect')
    def _connect(
            self, machine_name, port_name, driver_name, profile_name,
            persistent):
        machine = self._server.connect(
            self, machine_name, port_name, driver_name, profile_name,
            persistent)
        result = machine.to_dict()
        return result

    @jsonrpc('disconnect')
    def _disconnect(self, machine_name):
        pass

    @jsonrpc('pause')
    def _pause(self, machine_name):
        pass

    @jsonrpc('unpause')
    def _unpause(self, machine_name):
        pass

    def _load_services(self):
        conveyor.jsonrpc.install(self._jsonrpc, self)

    def run(self):
        try:
            self._load_services()
            self._server.appendclientthread(self)
            try:
                self._jsonrpc.run()
            finally:
                self._server.removeclientthread(self)
                self._jsonrpc.close()
        except:
            self._log.exception('unhandled exception')

    def stop(self):
        self._jsonrpc.stop()

class Queue(object):
    def __init__(self):
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._log = logging.getLogger(self.__class__.__name__)
        self._queue = collections.deque()
        self._stop = False

    def _runiteration(self):
        with self._condition:
            if 0 == len(self._queue):
                self._log.debug('waiting')
                self._condition.wait()
                self._log.debug('resumed')
            if 0 == len(self._queue):
                self._log.debug('queue is empty')
                func = None
            else:
                self._log.debug('queue is not empty')
                func = self._queue.pop()
        if None is not func:
            try:
                self._log.debug('running func')
                func()
                self._log.debug('func ended')
            except:
                self._log.exception('unhandled exception')

    def appendfunc(self, func):
        with self._condition:
            self._queue.appendleft(func)
            self._condition.notify_all()

    def run(self):
        self._log.debug('starting')
        self._stop = False
        while not self._stop:
            self._runiteration()
        self._log.debug('ending')

    def stop(self):
        with self._condition:
            self._stop = True
            self._condition.notify_all()

class _TaskQueueThread(threading.Thread, conveyor.stoppable.StoppableInterface):
    def __init__(self, queue):
        threading.Thread.__init__(self, name='taskqueue')
        conveyor.stoppable.StoppableInterface.__init__(self)
        self._log = logging.getLogger(self.__class__.__name__)
        self._queue = queue

    def run(self):
        try:
            self._queue.run()
        except:
            self._log.error('internal error', exc_info=True)

    def stop(self):
        self._queue.stop()


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


class Server(object):
    def __init__(
            self, config, driver_manager, port_manager, machine_manager,
            spool, connection_manager, listener):
        self._config = config
        self._driver_manager = driver_manager
        self._port_manager = port_manager
        self._machine_manager = machine_manager
        self._spool = spool
        self._connection_manager = connection_manager
        self._listener = listener
        self._clientthreads = []
        self._idcounter = 0
        self._jobcounter = 0
        self._jobs = {}
        self._job_dicts = {}
        self._lock = threading.Lock()
        self._log = logging.getLogger(self.__class__.__name__)
        self._queue = Queue()
        self._printerthreads = {}

    def _invokeclients(self, methodname, *args, **kwargs):
        with self._lock:
            clientthreads = self._clientthreads[:]
        for clientthread in clientthreads:
            try:
                method = getattr(clientthread, methodname)
                method(*args, **kwargs)
            except conveyor.connection.ConnectionWriteException:
                self._log.debug('handled exception', exc_info=True)
                clientthread.stop()
            except:
                self._log.exception('unhandled exception')

    def getprinterthreads(self):
        with self._lock:
            printerthreads = self._printerthreads.copy()
        return printerthreads

    def findprinter_printerid(self, name):
        with self._lock:
            for printerthread in self._printerthreads.values():
                if name == printerthread.getprinterid():
                    return printerthread
            return None

    def findprinter_portname(self, name):
        with self._lock:
            for printerthread in self._printerthreads.values():
                if name == printerthread.getportname():
                    return printerthread
            return None

    # NOTE: the difference between createjob and addjob is that createjob
    # creates a new job domain object while add job takes a job domain object,
    # adds it to the list of jobs, and notifies connected clients.
    #
    # The job created by createjob will have None as its process. The job
    # passed to addjob must have a valid process.

    def createjob(
        self, build_name, path, config, printerid, profile, gcodeprocessor,
        skip_start_end, with_start_end, slicer_settings, print_to_file_type, material):
            # NOTE: The profile is not currently included in the actual job
            # because it can't be converted to or from JSON.
            with self._lock:
                id = self._jobcounter
                self._jobcounter += 1
                job = conveyor.domain.Job(
                    id, build_name, path, config, printerid, gcodeprocessor,
                    skip_start_end, with_start_end, slicer_settings, print_to_file_type, material)
                return job

    def addjob(self, job):
        with self._lock:
            self._jobs[job.id] = job
        dct = job.todict()
        self._invokeclients('jobadded', dct)

    def changejob(self, job):
        params = job.todict()
        if job.id not in self._job_dicts:
            send = True
        else:
            old_params = self._job_dicts[job.id]
            send = old_params != params
        if send:
            self._job_dicts[job.id] = params
            self._invokeclients("jobchanged", params)
            task = job.process
            childtask = task.progress
            progress = childtask.progress
            self._log.info('progress: (job %d) %r', job.id, progress)

    def canceljob(self, id):
        with self._lock:
            job = self._jobs[id]
        if conveyor.task.TaskState.STOPPED != job.process.state:
            job.process.cancel()

    def getjobs(self):
        with self._lock:
            jobs = self._jobs.copy()
            return jobs

    def getjob(self, id):
        with self._lock:
            job = self._jobs[id]
            return job

    def appendclientthread(self, clientthread):
        with self._lock:
            self._clientthreads.append(clientthread)

    def removeclientthread(self, clientthread):
        with self._lock:
            self._clientthreads.remove(clientthread)

    def appendprinter(self, portname, printerthread):
        self._log.info('printer connected: %s', portname)
        with self._lock:
            self._printerthreads[portname] = printerthread
        printerid = printerthread.getprinterid()
        profile = printerthread.getprofile()
        firmware_version = printerthread.get_firmware_version()
        printer = conveyor.domain.Printer.fromprofile(
            profile, printerid, None, firmware_version)
        dct = printer.todict()
        self._invokeclients('printeradded', dct)

    def changeprinter(self, portname, temperature):
        self._log.debug('portname=%r, temperature=%r', portname, temperature)
        printerthread = self.findprinter_portname(portname)
        printerid = printerthread.getprinterid()
        profile = printerthread.getprofile()
        firmware_version = printerthread.get_firmware_version()
        printer = conveyor.domain.Printer.fromprofile(
            profile, printerid, temperature, firmware_version)
        dct = printer.todict()
        self._invokeclients('printerchanged', dct)

    def removeprinter(self, portname):
        self._log.info('printer disconnected: %s', portname)
        with self._lock:
            if portname in self._printerthreads:
                printerthread = self._printerthreads.pop(portname)
            else:
                printerthread = None
        if None is printerthread:
            self._log.debug(
                'disconnected unconnected printer: %s', portname)
        else:
            printerthread.stop()
            printerid = printerthread.getprinterid()
            params = {'id': printerid}
            self._invokeclients('printerremoved', params)

    def printtofile(self, profile, buildname, inputpath, outputpath,
            slicer_settings, print_to_file_type, material,
            task, dualstrusion):
        def func():
            driver = conveyor.machine.s3g.S3gDriver()
            driver.printtofile(
                outputpath, profile, buildname, inputpath, 
                slicer_settings, print_to_file_type, material, task,
                dualstrusion)
        self._queue.appendfunc(func)

    def slice(
        self, profile, inputpath, outputpath, with_start_end,
        slicer_settings, material, dualstrusion, task):
            def func():
                if conveyor.domain.Slicer.MIRACLEGRUE == slicer_settings.slicer:
                    slicerpath = self._config.get('miracle_grue', 'exe')
                    profiledir = self._config.get('miracle_grue', 'profile_dir')
                    slicer = conveyor.slicer.miraclegrue.MiracleGrueSlicer(
                        profile, inputpath, outputpath, with_start_end,
                        slicer_settings, material, dualstrusion, task,
                        slicerpath, profiledir)
                elif conveyor.domain.Slicer.SKEINFORGE == slicer_settings.slicer:
                    slicerpath = self._config.get('skeinforge', 'exe')
                    profiledir = self._config.get('skeinforge', 'profile_dir')
                    slicer = conveyor.slicer.skeinforge.SkeinforgeSlicer(
                        profile, inputpath, outputpath, with_start_end,
                        slicer_settings, material, dualstrusion, task,
                        slicerpath, profilepath)
                else:
                    raise ValueError(slicer_settings.slicer)
                slicer.slice()
            self._queue.appendfunc(func)

    def machine_connected(self, machine):
        pass # TODO

    def connect(
            self, client, machine_name, port_name, driver_name, profile_name,
            persistent):
        if None is not machine_name:
            machine = self._machine_manager.get_machine(machine_name)
            port = machine.get_port()
            if None is not port_name and port_name != port.name:
                raise conveyor.error.PortMismatchException
        else:
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
            machine = port.get_machine()
        if None is not machine:
            driver = machine.get_driver()
            if None is not driver_name and driver_name != driver.name:
                raise conveyor.error.DriverMismatchException
        elif None is not driver_name:
            driver = self._driver_manager.get_driver(driver_name)
        else:
            if 0 == len(port.driver_profiles):
                raise conveyor.error.NoDriversException
            elif len(port.driver_profiles) > 1:
                raise MultipleDriversException
            else:
                # NOTE: this loop extracts the single driver.
                for driver_name in port.driver_profiles.keys():
                    driver = self._driver_manager.get_driver(driver_name)
        if None is not machine:
            profile = machine.get_profile()
            if None is not profile_name and profile_name != profile.name:
                raise conveyor.error.ProfileMismatchException
        elif None is not profile_name:
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
        if None is machine:
            machine = self._machine_manager.new_machine(port, driver, profile)
            machine.set_port(port)
            port.set_machine(machine)
        if conveyor.machine.MachineState.DISCONNECTED == machine.get_state():
            machine.connect()
            self.machine_connected(machine)
        self._connection_manager.acquire_machine(client, machine, persistent)
        return machine

    def run(self):
        taskqueuethread = _TaskQueueThread(self._queue)
        taskqueuethread.start()
        try:
            while True:
                connection = self._listener.accept()
                with self._lock:
                    id = self._idcounter
                    self._idcounter += 1
                clientthread = _ClientThread.create(
                    self._config, self, connection, id)
                clientthread.start()
        finally:
            self._queue.stop()
            taskqueuethread.join(1)
        return 0
