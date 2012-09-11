# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/printer/s3g.py
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
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._detector = makerbot_driver.MachineDetector()
        self._log = logging.getLogger(self.__class__.__name__)
        self._server = server
        self._stop = False

    def _runiteration(self):
        profiledir = self._config['common']['profiledir']
        factory = makerbot_driver.BotFactory(profiledir)
        now = time.time()
        for portname, unlisttime in self._blacklist.items():
            if now >= unlisttime:
                del self._blacklist[portname]
                self._log.debug('removing port from blacklist: %r', portname)
        available = self._detector.get_available_machines().copy()
        self._log.debug('available = %r', available)
        self._log.debug('blacklist = %r', self._blacklist)
        old_keys = set(self._available.keys())
        new_keys = set(available.keys())
        detached = old_keys - new_keys
        attached = new_keys - old_keys - set(self._blacklist.keys())
        self._log.debug('detached = %r', detached)
        self._log.debug('attached = %r', attached)
        for portname in detached:
            self._server.removeprinter(portname)
        if len(attached) > 0:
            for portname in attached:
                try:
                    s3g, profile = factory.build_from_port(portname, True)
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
        self._available = available

    def blacklist(self, portname):
        if portname in self._available:
            del self._available[portname]
        now = time.time()
        unlisttime = now + self._config['server']['blacklisttime']
        self._blacklist[portname] = unlisttime

    def run(self):
        try:
            while not self._stop:
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
        material, task):
            def stoppedcallback(task):
                with self._condition:
                    self._currenttask = None
                    self._curprintjob = None
                    self._statetransition("printing", "idle")
            task.stoppedevent.attach(stoppedcallback)
            self._log.debug(
                'job=%r, buildname=%r, gcodepath=%r, skip_start_end=%r, slicer_settings=%r, material=%r, task=%r',
                job, buildname, gcodepath, skip_start_end, slicer_settings,
                material, task)
            with self._condition:
                printjob = (
                    job, buildname, gcodepath, skip_start_end,
                    slicer_settings, material, task)
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
                    job, buildname, gcodepath, skip_start_end, slicer_settings, material, task = self._curprintjob
                    driver = S3gDriver()
                    try:
                        with self._condition:
                            self._statetransition("idle", "printing")
                            self._currenttask = task
                        driver.print(
                            self._server, self._portname, self._fp,
                            self._profile, buildname, gcodepath,
                            skip_start_end, slicer_settings, material, task)
                    except PrinterThreadNotIdleError:
                        pass
                    except makerbot_driver.BuildCancelledError:
                        self._log.debug('handled exception', exc_info=True)
                        self._log.info('print canceled')
                        with self._condition:
                            if None is not self._currenttask:
                                self._currenttask.cancel()
                    except Exception as e:
                        self._log.error('unhandled exception', exc_info=True)
                        with self._condition:
                            if None is not self._currenttask:
                                self._currenttask.fail(e)
                  
        except:
            self._log.exception('unhandled exception')
            self._server.evictprinter(self._portname, self._fp)
        finally:
            self._fp.close()

    def readeeprom(self):
        driver = S3gDriver()
        with self._condition:
            self._statetransition("idle", "readingeeprom")
            eeprommap = driver.readeeprom(self._fp)
            self._statetransition("readingeeprom", "idle")
        return eeprommap

    def writeeeprom(self, eeprommap, task):
        with self._condition:
            self._statetransition("idle", "writingeeprom")
        def stoppedcallback(task):
            with self._condition:
                self._statetransition("writingeeprom", "idle")
                self._currenttask = None
            task.end(None)
        def runningcallback(task):
            driver = S3gDriver()
            with self._condition:
                driver.writeeeprom(eeprommap, self._fp)
            task.end(None)
        task.stoppedevent.attach(stoppedcallback)
        task.runningevent.attach(runningcallback)
        with self._condition:
            self._currenttask = task
            self._currenttask.start()


    def uploadfirmware(self, machine_type, version, task):
        with self._condition:
            self._statetransition("idle", "uploadingfirmware")
        def stoppedcallback(task):
            self._statetransition("uploadingfirmware", "idle")
            self._currenttask = None
        def runningcallback(task):
            uploader = makerbot_driver.Firmware.Uploader()
            with self._condition:
                self._fp.close()
                try:
                    uploader.upload_firmware(self._fp.port, machine_type, version)
                    task.end(None)
                except makerbot_driver.Firmware.subprocess.CalledProcessError as e:
                    task.fail(e) 
                finally:
                    self._fp.open()
        task.runningevent.attach(runningcallback)
        task.stoppedevent.attach(stoppedcallback)
        with self._condition:
            self._currenttask = task
            self._currenttask.start()

    def resettofactory(self):
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
        with self._condition:
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

    def _get_start_end_variables(self, profile, slicer_settings, material):
        if None is material:
            material = 'PLA'
        ga = makerbot_driver.GcodeAssembler(profile, profile.path)
        start_template, end_template, variables = ga.assemble_recipe(material=material)
        start_gcode = ga.assemble_start_sequence(start_template)
        end_gcode = ga.assemble_end_sequence(end_template)
        variables['TOOL_0_TEMP'] = slicer_settings.extruder_temperature
        variables['TOOL_1_TEMP'] = slicer_settings.extruder_temperature
        variables['PLATFORM_TEMP'] = slicer_settings.platform_temperature
        return start_gcode, end_gcode, variables

    def _gcodelines(
        self, profile, gcodepath, skip_start_end, slicer_settings, material):
            startgcode, endgcode, variables = self._get_start_end_variables(
                profile, slicer_settings, material)
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

    def _update_progress(self, current_progress, new_progress, task):
        if None is not new_progress and new_progress != current_progress:
            current_progress = new_progress
            task.heartbeat(current_progress)
        return current_progress

    def _genericprint(
        self, server, portname, profile, buildname, writer, polltemperature,
        pollinterval, gcodepath, skip_start_end, slicer_settings, material,
        task):
            current_progress = None
            new_progress = {
                'name': 'print',
                'progress': 0
            }
            current_progress = self._update_progress(
                current_progress, new_progress, task)
            def stoppedcallback(task):
                writer.set_external_stop()
            task.stoppedevent.attach(stoppedcallback)
            parser = makerbot_driver.Gcode.GcodeParser()
            parser.state.profile = profile
            parser.state.set_build_name(str(buildname))
            parser.s3g = makerbot_driver.s3g()
            parser.s3g.writer = writer
            def stoppedcallback(task):
                #Reset the bot
                parser.s3g.abort_immediately()
                writer.set_external_stop()
            task.stoppedevent.attach(stoppedcallback)
            now = time.time()
            polltime = now + pollinterval
            if not polltemperature:
                temperature = None
            else:
                temperature = _gettemperature(profile, parser.s3g)
                server.changeprinter(portname, temperature)
            gcodelines, variables = self._gcodelines(
                profile, gcodepath, skip_start_end, slicer_settings, material)
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
                    try:
                        parser.execute_line(data)
                    except makerbot_driver.Writer.ExternalStopError:
                        self._log.debug('handled exception', exc_info=True)
                        self._log.info('print canceled')
                        with self._condition:
                            if None is not self._currenttask:
                                self._currenttask.cancel()
                    new_progress = {
                        'name': 'print',
                        'progress': int(parser.state.percentage)
                    }
                    if polltime <= now:
                        polltime = now + pollinterval
                        if polltemperature:
                            server.changeprinter(portname, temperature)
                    current_progress = self._update_progress(
                        current_progress, new_progress, task)
            if conveyor.task.TaskState.STOPPED != task.state:
                new_progress = {
                    'name': 'print',
                    'progress': 100
                }
                current_progress = self._update_progress(
                    current_progress, new_progress, task)
                task.end(None)

    def print(
        self, server, portname, fp, profile, buildname, gcodepath,
        skip_start_end, slicer_settings, material, task):
            writer = makerbot_driver.Writer.StreamWriter(fp)
            self._genericprint(
                server, portname, profile, buildname, writer, True, 5.0,
                gcodepath, skip_start_end, slicer_settings, material, task)

    def printtofile(
        self, outputpath, profile, buildname, gcodepath, skip_start_end,
        slicer_settings, material, task):
            with open(outputpath, 'wb') as fp:
                writer = makerbot_driver.Writer.FileWriter(fp)
                self._genericprint(
                    None, None, profile, buildname, writer, False, 5.0,
                    gcodepath, skip_start_end, slicer_settings, material,
                    task)

    def resettofactory(
        self, fp):
            s = self.create_s3g_from_fp(fp)
            s.reset_to_factory()
            return True

    def writeeeprom(
        self, eeprommap, fp):
            s = self.create_s3g_from_fp(fp)
            version = str(s.get_version())
            version = version.replace('0', '.')
            eeprom_writer = makerbot_driver.EEPROM.EepromWriter.factory(s, version)
            eeprom_writer.write_entire_map(eeprommap)
            return True

    def readeeprom(
        self, fp):
            s = self.create_s3g_from_fp(fp)
            version = str(s.get_version())
            version = version.replace('0', '.')
            eeprom_reader = makerbot_driver.EEPROM.EepromReader.factory(s, version)
            the_map = eeprom_reader.read_entire_map()
            return the_map

    def create_s3g_from_fp(self, fp):
        s = makerbot_driver.s3g()
        s.writer = makerbot_driver.Writer.StreamWriter(fp)
        return s
