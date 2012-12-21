# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4
# conveyor/src/main/python/conveyor/machine/s3g.py
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
import makerbot_driver.Writer
import os.path
import serial
import threading
import time

import conveyor.event
import conveyor.task

class S3gDetectorThread(conveyor.stoppable.StoppableThread):
    def __init__(self, config, server):
        conveyor.stoppable.StoppableThread.__init__(self)
        self._available = {}
        self._blacklist = {}
        self._config = config
        self._condition = threading.Condition()
        self._detector = makerbot_driver.MachineDetector()
        self._log = logging.getLogger(self.__class__.__name__)
        self._server = server
        self._stop = False

    def _expire_blacklist(self):
        now = time.time()
        for portname, unlisttime in self._blacklist.items():
            if now >= unlisttime:
                del self._blacklist[portname]
                self._log.debug('removing port from blacklist: %r', portname)

    def _runiteration(self):
        self._expire_blacklist()
        profiledir = self._config['common']['profiledir']
        factory = makerbot_driver.MachineFactory(profiledir)
        available = self._detector.get_available_machines().copy()
        self._log.debug('self._available = %r', self._available)
        self._log.debug('available = %r', available)
        self._log.debug('blacklist = %r', self._blacklist)
        for portname in self._blacklist.keys():
            if portname in available:
                del available[portname]
        self._log.debug('available (post blacklist) = %r', available)
        old_keys = set(self._available.keys())
        new_keys = set(available.keys())
        detached = old_keys - new_keys
        attached = new_keys - old_keys
        self._log.debug('detached = %r', detached)
        self._log.debug('attached = %r', attached)
        for portname in detached:
            self._server.removeprinter(portname)
        if len(attached) > 0:
            for portname in attached:
                try:
                    returnobj = factory.build_from_port(portname, True)
                    s3g = getattr(returnobj, 's3g')
                    profile = getattr(returnobj, 'profile')
                    printerid = available[portname]['iSerial']
                    fp = s3g.writer.file
                    s3gprinterthread = S3gPrinterThread(
                        self._server, self._config, portname, printerid, profile,
                        fp)
                    s3gprinterthread.start()
                    self._server.appendprinter(portname, s3gprinterthread)
                except:
                    self._log.exception('unhandled exception')
                    self.blacklist(portname)
        self._available = available.copy()

    def blacklist(self, portname):
        with self._condition:
            if portname in self._available:
                del self._available[portname]
            now = time.time()
            unlisttime = now + self._config['server']['blacklisttime']
            self._blacklist[portname] = unlisttime

    def run(self):
        try:
            while not self._stop:
                with self._condition:
                    self._runiteration()
                if not self._stop:
                    with self._condition:
                        self._condition.wait(10.0)
        except:
            self._log.error('unhandled exception', exc_info=True)

    def stop(self):
        with self._condition:
            self._stop = True
            self._condition.notify_all()

def _gettemperature(profile, s3g):
    tools = {}
    for key in profile.values['tools'].keys():
        tool = int(key)
        tools[key] = s3g.get_toolhead_temperature(tool)
    heated_platforms = {}
    for key in profile.values['heated_platforms'].keys():
        heated_platform = int(key)
        heated_platforms[key] = s3g.get_platform_temperature(heated_platform)
    temperature = {
        'tools': tools,
        'heated_platforms': heated_platforms
    }
    return temperature

class PrinterThreadNotIdleError(Exception):
    def __init__(self):
        pass

class PrinterThreadBadStateError(Exception):
    def __init__(self):
        pass

class S3gPrinterThread(conveyor.stoppable.StoppableThread):
    def __init__(self, server, config, portname, printerid, profile, fp):
        conveyor.stoppable.StoppableThread.__init__(self)
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._config = config
        self._currenttask = None
        self._fp = fp
        self._log = logging.getLogger(self.__class__.__name__)
        self._portname = portname
        self._printerid = printerid
        self._profile = profile
        self._queue = collections.deque()
        self._server = server
        self._stop = False
        self._curprintjob = None

        #states
        self._states = {
            "idle" : True,
            "printing"  : False,
            "uploadingfirmware"  : False,
            "readingeeprom"  : False,
            "writingeeprom"  : False,
            "resettofactory" : False,
            }

    def _statetransition(self, current, new):
        #The current state should be true
        if not self._states[current]:
            self._log.info("error=printer_thread_not_idle, action=%s", new)
            raise PrinterThreadNotIdleError
        self._states[current] = False
        #All states should be false at this point
        if True in self._states.values():
            self._log.info("error=bad_printer_thread_state, action=%s", new)
            raise PrinterThreadBadStateError
        self._states[new] = True
        self._log.debug('oldstate=%s, newstate=%s', current, new)

    def getportname(self):
        return self._portname

    def getprinterid(self):
        return self._printerid

    def getprofile(self):
        return self._profile

    def print(
        self, job, buildname, gcodepath, skip_start_end, slicer_settings,
        print_to_file_type, material, task, dualstrusion):
            def stoppedcallback(task):
                with self._condition:
                    self._currenttask = None
                    self._curprintjob = None
                    self._statetransition("printing", "idle")
            task.stoppedevent.attach(stoppedcallback)
            self._log.debug(
                'job=%r, buildname=%r, gcodepath=%r, skip_start_end=%r, slicer_settings=%r, material=%r, task=%r',
                job, buildname, gcodepath, skip_start_end, slicer_settings,
                print_to_file_type, material, task)
            with self._condition:
                printjob = (
                    job, buildname, gcodepath, skip_start_end,
                    slicer_settings, print_to_file_type, material, task,
                    dualstrusion)
                self._queue.appendleft(printjob)
                self._condition.notify_all()

    def run(self):
        try:
            s3g = makerbot_driver.s3g()
            s3g.writer = makerbot_driver.Writer.StreamWriter(self._fp)
            now = time.time()
            polltime = now + 5.0
            while not self._stop:
                if self._states['idle'] and self._curprintjob is None:
                    with self._condition:
                        if 0 < len(self._queue):
                            self._curprintjob = self._queue.pop()
                    now = time.time()
                    if polltime <= now:
                        polltime = now + 5.0
                        try:
                            with self._condition: # TODO: this is a hack
                                temperature = _gettemperature(self._profile, s3g)
                        except makerbot_driver.BuildCancelledError:
                            self._log.debug('handled exception', exc_info=True)
                            # This happens when print from SD and cancel it on
                            # the bot. There is no conveyor job to cancel.
                        else:
                            self._server.changeprinter(
                                self._portname, temperature)
                    with self._condition:
                        self._log.debug('waiting')
                        self._condition.wait(1.0)
                        self._log.debug('resumed')
                elif self._states['idle'] and self._curprintjob is not None:
                    job, buildname, gcodepath, skip_start_end, slicer_settings, print_to_file_type, material, task, dualstrusion = self._curprintjob
                    driver = S3gDriver()
                    try:
                        with self._condition:
                            self._statetransition("idle", "printing")
                            self._currenttask = task
                        driver.print(
                            self._server, self._portname, self._fp,
                            self._profile, buildname, gcodepath,
                            skip_start_end, slicer_settings,
                            print_to_file_type, material, task, dualstrusion)
                    except PrinterThreadNotIdleError:
                        self._log.debug('handled exception', exc_info=True)
                    except makerbot_driver.BuildCancelledError:
                        self._log.debug('handled exception', exc_info=True)
                        self._log.info('print canceled')
                        if (None is not self._currenttask
                            and conveyor.task.TaskState.STOPPED != self._currenttask.state):
                                with self._condition:
                                    self._currenttask.cancel()
                    except makerbot_driver.ExternalStopError:
                        self._log.debug('handled exception', exc_info=True)
                        self._log.info('print canceled')
                        if (None is not self._currenttask
                            and conveyor.task.TaskState.STOPPED != self._currenttask.state):
                                with self._condition:
                                    self._currenttask.cancel()
                    except Exception as e:
                        self._log.error('unhandled exception', exc_info=True)
                        with self._condition:
                            if None is not self._currenttask:
                                self._currenttask.fail(e)
                    now = time.time()
                    polltime = now + 5.0
        except:
            self._log.exception('unhandled exception')
            self._server.evictprinter(self._portname, self._fp)
        finally:
            self._fp.close()

    def readeeprom(self, task):
        driver = S3gDriver()
        with self._condition:
            self._statetransition("idle", "readingeeprom")
            self._currenttask = task
            try:
                eeprommap = driver.readeeprom(self._fp)
                return eeprommap
            finally:
                self._statetransition("readingeeprom", "idle")
                self._currenttask = None

    def writeeeprom(self, eeprommap, task):
        driver = S3gDriver()
        with self._condition:
            self._statetransition("idle", "writingeeprom")
            self._currenttask = task
            try:
                driver.writeeeprom(eeprommap, self._fp)
            finally:
                self._statetransition("writingeeprom", "idle")
                self._currenttask = None
    
    def uploadfirmware(self, machine_type, filename, task):
        with self._condition:
            self._statetransition("idle", "uploadingfirmware")
            uploader = makerbot_driver.Firmware.Uploader()
            self._fp.close()
            try:
                uploader.upload_firmware(self._portname, machine_type, filename)
            finally:
                self._fp.open()
                self._statetransition("uploadingfirmware", "idle")
                self._currenttask = None

    def resettofactory(self, task):
        with self._condition:
            self._statetransition("idle", "resettofactory")
            def stoppedcallback(task):
                self._statetransition("resettofactory", "idle")
                self._currenttask = None
            def runningcallback(task):
                driver = S3gDriver()
                with self._condition:
                    driver.resettofactory(self._fp)
                task.end(None)
            task.stoppedevent.attach(stoppedcallback)
            task.runningevent.attach(runningcallback)
            self._currenttask = task
            self._currenttask.start()

    def stop(self):
        with self._condition:
            self._stop = True
            if None is not self._currenttask:
                self._currenttask.cancel()
            self._condition.notify_all()

class S3gDriver(object):
    '''Stateless S3G printer driver.

    All of the state related to a print job is passed on the call stack.
    Instances of this class can safely be used by multiple threads.
    '''

    def __init__(self):
        self._log = logging.getLogger(self.__class__.__name__)

    # TODO: It makes me sad that we pass "slicer"_settings here, but that's the
    # object that has the extruder and platform temperatures. Domain modeling
    # error.

    def _get_start_end_variables(self, profile, slicer_settings, material, dualstrusion):
        """
        @returns tuple of (start gcode block, end gcode block, variables)
        """
        tool_0, tool_1 = False, False
        if None is material:
            material = 'PLA'
        if dualstrusion:
            tool_0 = True
            tool_1 = True
        else:
            extruders = [e.strip() for e in slicer_settings.extruder.split(',')]
            if '0' in extruders:
                tool_0 = True
            if '1' in extruders:
                tool_1 = True
        ga = makerbot_driver.GcodeAssembler(profile, profile.path)
        start_template, end_template, variables = ga.assemble_recipe(
            tool_0=tool_0, tool_1=tool_1, material=material)
        start_gcode = ga.assemble_start_sequence(start_template)
        end_gcode = ga.assemble_end_sequence(end_template)
        variables['TOOL_0_TEMP'] = slicer_settings.extruder_temperature
        variables['TOOL_1_TEMP'] = slicer_settings.extruder_temperature
        variables['PLATFORM_TEMP'] = slicer_settings.platform_temperature
        return start_gcode, end_gcode, variables

    def _gcodelines(self, profile, gcodepath, skip_start_end, slicer_settings,
            material, dualstrusion):
        """
        @profle: undocumented, assuming a profile object
        @gcodepath: undocumented assuming filepath
        @skip_start_end: bool, True to skip start/end gcode bookends
        @slicer_settings: undocumented. assuming dict
        @material undocumneted, assuming string
        """ 
        startgcode, endgcode, variables = self._get_start_end_variables(
                profile, slicer_settings, material, dualstrusion)
        def generator():
            if not skip_start_end:
                if None is not startgcode:
                    for data in startgcode:
                        yield data
            with open(gcodepath, 'r') as fp:
                for data in fp:
                    yield data
            if not skip_start_end:
                if None is not endgcode:
                    for data in endgcode:
                        yield data
        gcodelines = list(generator())
        return gcodelines, variables

    def _countgcodelines(self, gcodelines):
        lines = 0
        bytes = 0
        for data in enumerate(gcodelines):
            lines += 1
            bytes += len(data)
        return (lines, bytes)

    def _genericprint(self, server, portname, profile, buildname, writer,
            polltemperature, pollinterval, gcodepath, skip_start_end,
            slicer_settings, print_to_file_type, material, task,
            dualstrusion):
        """
        This does a generic print? 
        @param server conveyor.server object
        @param portname undocumneted. assuming it's the os-specific port name string
        @param profile undocumented, assuming a profile object
        @param buildname build name
        @param writer   undocumented filewrite
        @param polltemperature bool, true to poll temperture at pollinterval
        @param pollinterval frequency of ?? poll, in seconds
        @param gcodepath unddocumented assuming string name of gcode file to print
        @param skip_start_end bool, set true to skip using start/end gcode
        @param slicer_settings undocumented assuming a slicer settings dict
        @param material a string indicating the material type
        @param task undocumented, assuming it's a task object
        """
        current_progress = None
        new_progress = {
            'name': 'print',
            'progress': 0
        }
        task.lazy_heartbeat(current_progress, new_progress)
        current_progress, new_progress = new_progress, None
        parser = makerbot_driver.Gcode.GcodeParser()
        # ^ Technical debt: we should not be reaching 'into' objects in our 
        # driver, and manually setting state info, etc. Those should be 
        # constructor params
        parser.state.profile = profile
        parser.state.set_build_name(str(buildname))
        parser.s3g = makerbot_driver.s3g()
        parser.s3g.writer = writer
        if print_to_file_type is not None:
            parser.s3g.set_print_to_file_type(print_to_file_type);
        # ^ Technical debt: we should no be reacing into objects in our driver to 
        # set values, they should be set in the constructor
        def cancelcallback(task):
            """Stop the writer and catch an ExternalStopError."""
            try:
                self._log.debug('setting external stop')
                writer.set_external_stop()
            except makerbot_driver.ExternalStopError:
                self._log.debug('handled exception', exc_info=True)
            if polltemperature:
                self._log.debug('aborting printer')
                # NOTE: need a new s3g object because the old one has
                # external stop set.
                # TODO: this is a horrible hack.
                s3g = makerbot_driver.s3g()
                s3g.writer = makerbot_driver.Writer.StreamWriter(
                    parser.s3g.writer.file)
                s3g.abort_immediately()
        task.cancelevent.attach(cancelcallback)
        if polltemperature:
            self._log.debug('resetting machine %s', portname)
            parser.s3g.reset()
        now = time.time()
        polltime = now + pollinterval
        if not polltemperature:
            temperature = None
        else:
            temperature = _gettemperature(profile, parser.s3g)
            server.changeprinter(portname, temperature)
        # Send the start of stream command for x3g bots
        if print_to_file_type == 'x3g':
            pid = parser.state.profile.values['PID']
            # ^ Technical debt: we get this value from conveyor local bot info, not from the profile
            parser.s3g.x3g_version(1, 0, pid=pid) # Currently hardcode x3g v1.0
        gcodelines, variables = self._gcodelines(
            profile, gcodepath, skip_start_end, slicer_settings, material,
            dualstrusion)
        parser.environment.update(variables)
        # TODO: remove this {current,total}{byte,line} stuff; we have
        # proper progress from the slicer now.
        totallines, totalbytes = self._countgcodelines(gcodelines)
        currentbyte = 0
        for currentline, data in enumerate(gcodelines):
            if conveyor.task.TaskState.RUNNING != task.state:
                break
            else:
                # Increment currentbyte *before* stripping whitespace
                # out of data or the currentbyte will not match the
                # actual file position.
                currentbyte += len(data)
                data = data.strip()
                now = time.time()
                if polltemperature and polltime <= now:
                    temperature = _gettemperature(profile, parser.s3g)
                self._log.debug('gcode: %r', data)
                # The s3g module cannot handle unicode strings.
                data = str(data)
                parser.execute_line(data)
                new_progress = {
                    'name': 'print',
                    'progress': int(parser.state.percentage)
                }
                if polltime <= now:
                    polltime = now + pollinterval
                    if polltemperature:
                        server.changeprinter(portname, temperature)
                task.lazy_heartbeat(current_progress, new_progress)
                current_progress, new_progress = new_progress, None
        if polltemperature:
            '''
            # This is the code that should be, but it requires new
            # firmware.
            while conveyor.task.TaskState.STOPPED != task.state:
                build_stats = parser.s3g.get_build_stats()
                build_state = build_stats['BuildState']
                self._log.debug('build_stats=%r', build_stats)
                self._log.debug('build_state=%r', build_state)
                if 0 == build_state or 2 == build_state or 4 == build_state: # TODO: constants for these magic codes
                    break
                else:
                    time.sleep(0.2) # TODO: wait on a condition
            '''
            while conveyor.task.TaskState.STOPPED != task.state:
                available = parser.s3g.get_available_buffer_size()
                if 512 == available:
                    break
                else:
                    time.sleep(0.2) # TODO: wait on a condition
            if conveyor.task.TaskState.STOPPED != task.state:
                new_progress = {
                    'name': 'print',
                    'progress': int(parser.state.percentage)
                }
                if polltime <= now:
                    polltime = now + pollinterval
                    if polltemperature:
                        server.changeprinter(portname, temperature)
                task.lazy_heartbeat(current_progress, new_progress)
                current_progress, new_progress  = new_progress, None
        if polltemperature:
            '''
            # This is the code that should be, but it requires new
            # firmware.
            while conveyor.task.TaskState.STOPPED != task.state:
                build_stats = parser.s3g.get_build_stats()
                build_state = build_stats['BuildState']
                self._log.debug('build_stats=%r', build_stats)
                self._log.debug('build_state=%r', build_state)
                if 0 == build_state or 2 == build_state or 4 == build_state: # TODO: constants for these magic codes
                    break
                else:
                    time.sleep(0.2) # TODO: wait on a condition
            '''
            while conveyor.task.TaskState.STOPPED != task.state:
                available = parser.s3g.get_available_buffer_size()
                if 512 == available:
                    break
                else:
                    time.sleep(0.2) # TODO: wait on a condition

        if conveyor.task.TaskState.STOPPED != task.state:
            new_progress = {
                'name': 'print',
                'progress': 100
            }
            task.lazy_heartbeat(current_progress,new_progress)
            current_progress, new_progress = new_progress,None
            task.end(None)

    def print(self, server, portname, fp, profile, buildname, gcodepath,
            skip_start_end, slicer_settings, print_to_file_type, material,
            task, dualstrusion):
        """
        @param server conveyor.server object
        @param portname undocumneted. assuming it's the os-specific port name string
        @param fp undocumneted file pointer to  ???
        @param profile undocumented assuming a conveyor.Profile object
        @param buildname undocumented assuming the name of the build
        @param gcodepath unddocumented assuming string name of gcode file to print
        @param skip_start_end bool, set true to skip using start/end gcode
        @param slicer_settings undocumented assuming a slicer settings dict
        @param material a string indicating the material type
        @param task undocumented, assuming it's a task object
        """ 
        writer = makerbot_driver.Writer.StreamWriter(fp)
        self._genericprint(
            server, portname, profile, buildname, writer, True, 5.0,
            gcodepath, skip_start_end, slicer_settings, print_to_file_type,
            material, task, dualstrusion)

    def printtofile(self, outputpath, profile, buildname, gcodepath,
            skip_start_end, slicer_settings, print_to_file_type, material,
            task, dualstrusion):
        with open(outputpath, 'wb') as fp:
            writer = makerbot_driver.Writer.FileWriter(fp)
            self._genericprint(
                None, None, profile, buildname, writer, False, 5.0,
                gcodepath, skip_start_end, slicer_settings, print_to_file_type, material,
                task, dualstrusion)

    def resettofactory(self, fp):
        s = self.create_s3g_from_fp(fp)
        s.reset_to_factory()
        s.reset()
        return True

    def get_version_with_dot(self, version):
        # Log original version string
        self._log.debug('get_version: %r', version)

        # This assumes that the version string is always in 'XYY'
        # format, where X is the major version and YY is the minor
        # version. The EepromReader assumes that this will be
        # converted into an X.Y format. This is a bit ill-defined,
        # should clean this up (TODO)
        if len(version) == 3:
            if version[1] == '0':
                version = version[0] + '.' + version[2]
            else:
                version = version[0] + '.' + version[1:2]
        else:
            self._log.error('unexpected version length: %r', version)
        return version

        # Log modified version string
        self._log.debug('get_version: %r', version)

    def writeeeprom(
        self, eeprommap, fp):
            s = self.create_s3g_from_fp(fp)
            version = str(s.get_version())
            try:
                advanced_version_dict = s.get_advanced_version()
                software_variant = hex(advanced_version_dict['SoftwareVariant'])
                if len(software_variant.split('x')[1]) == 1:
                    software_variant = software_variant.replace('x', 'x0')
            except makerbot_driver.errors.CommandNotSupportedError:
                software_variant = '0x00'

            version = self.get_version_with_dot(version)

            eeprom_writer = makerbot_driver.EEPROM.EepromWriter.factory(s, version, software_variant)
            eeprom_writer.write_entire_map(eeprommap)
            return True

    def readeeprom(
        self, fp):
            s = self.create_s3g_from_fp(fp)
            version = str(s.get_version())
            try:
                advanced_version_dict = s.get_advanced_version()
                software_variant = hex(advanced_version_dict['SoftwareVariant'])
                if len(software_variant.split('x')[1]) == 1:
                    software_variant = software_variant.replace('x', 'x0')
            except makerbot_driver.errors.CommandNotSupportedError:
                software_variant = '0x00'

            version = self.get_version_with_dot(version)

            eeprom_reader = makerbot_driver.EEPROM.EepromReader.factory(s, version, software_variant)
            the_map = eeprom_reader.read_entire_map()
            return the_map

    def create_s3g_from_fp(self, fp):
        s = makerbot_driver.s3g()
        s.writer = makerbot_driver.Writer.StreamWriter(fp)
        return s

    def write_messages_to_display(self, s3gobj, messages, timeout, button_press, last_in_sequence):
        """
        Write messages to a machine.  If a message is too long, splits it in two and tries again.
        NB: We cast messages as strs, since makerbot_driver can't handle unicode well :(
        PNB: Since messages are just concatentated together, white-space needs to be baked into the messages.
        The screen we are writing to is 20x4

        @param s3g s3gobj: S3g object used to write messages
        @param string/unicode/tuple/list messages: Messages to write to the bot. If not passed as a list or tuple, forced into a list
        @param int timeout: Timeout for the messages.  Timeout = 0 displays indefinitely
        @param bool button_press: Flag for wait on button press.  If true, waits on a button press
        @param bool last_in_sequence: Flag to determine if this message is the last in a sequence.  Unless you want to send a 
            sequence of messages, this should be set to True
        """
        if not isinstance(messages, (list, tuple)):
            messages = [messages]
        for i in range(len(messages)):
            try:
                s3gobj.display_message(0, 0, str(messages[i]), timeout, True, False, False)
            # If the msg is too long, cut it in half and resend
            except makerbot_driver.errors.PacketLengthError as e:
                bifurcated_msg = self.split_message(messages[i])
                self.write_messages_to_display(s3gobj, bifurcated_msg, timeout, button_press, False)
        if last_in_sequence:
            s3gobj.display_message(0, 0, str(''), timeout, True, True, button_press)
        
    def split_message(self, msg):
        """
        Takes a msg and spits it in half.  If msg is of length 1 or less,
        returns a list containing only the msg

        @param str msg: Message to split
        @return list msgs: Split msg 
        """
        if len(msg) <= 1:
            msgs = [msg]
        else:
            msg_1 = msg[:len(msg)/2]
            msg_2 = msg[len(msg)/2:]
            msgs = [msg_1, msg_2]
        return msgs
