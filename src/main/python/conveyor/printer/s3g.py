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

import logging
import os.path
import s3g
import serial
import time

import conveyor.event
import conveyor.task

class S3gPrinter(object):
    def __init__(self, profile, device, baudrate):
        self._baudrate = baudrate
        self._device = device
        self._log = logging.getLogger(self.__class__.__name__)
        self._pollinterval = 5.0
        self._profile = profile

    def _gcodelines(self, gcodepath, skip_start_end=False):
        startgcode = self._profile.values['print_start_sequence']
        if None is not startgcode and not skip_start_end:
            for data in startgcode:
                yield data
        with open(gcodepath, 'r') as gcodefp:
            for data in gcodefp:
                yield data
        endgcode = self._profile.values['print_end_sequence']
        if None is not endgcode and not skip_start_end:
            for data in endgcode:
                yield data
    '''
    TODO: make this method work
        def _gcodelines(self, gcodepath, skip_start_end=False):
            if not skip_start_end: yield self._startlines()
            yield self._bodylines()
            if not skip_start_end: yield self._endlines()
    '''
    def _bodylines(self, gcodepath):
        with open(gcodepath, 'r') as gcodefp:
            for data in gcodefp:
                yield data
    def _startlines(self):
        startgcode = self._profile.values['print_start_sequence']
        if None is not startgcode:
            for data in startgcode:
                yield data
    def _endlines(self):
        endgcode = self._profile.values['print_end_sequence']
        if None is not endgcode:
            for data in endgcode:
                yield data
    def _countgcodelines(self, gcodepath, skip_start_end=False):
        lines = 0
        bytes = 0
        for data in enumerate(self._gcodelines(gcodepath, skip_start_end)):
            lines += 1
            bytes += len(data)
        return (lines, bytes)

    def _genericprint(self, task, writer, polltemperature, gcodepath, skip_start_end):
        parser = s3g.Gcode.GcodeParser()
        parser.state.profile = self._profile
        parser.state.set_build_name(str('xyzzy'))
        parser.s3g = s3g.s3g()
        parser.s3g.writer = writer
        now = time.time()
        polltime = now + self._pollinterval
        if polltemperature:
            platformtemperature = parser.s3g.get_platform_temperature(0)
            toolheadtemperature = parser.s3g.get_toolhead_temperature(0)
        totallines, totalbytes = self._countgcodelines(gcodepath, skip_start_end)
        currentbyte = 0
        for currentline, data in enumerate(self._gcodelines(gcodepath, skip_start_end)):
            currentbyte += len(data)
            now = time.time()
            if polltemperature:
                if polltime <= now:
                    platformtemperature = parser.s3g.get_platform_temperature(0)
                    toolheadtemperature = parser.s3g.get_toolhead_temperature(0)
                    self._log.info('platform temperature: %r', platformtemperature)
                    self._log.info('toolhead temperature: %r', toolheadtemperature)
            data = data.strip()
            self._log.info('gcode: %r', data)
            data = str(data)
            parser.execute_line(data)
            progress = {
                'currentline': currentline,
                'totallines': totallines,
                'currentbyte': currentbyte,
                'totalbytes': totalbytes,
            }
            if polltime <= now:
                polltime = now + self._pollinterval
                if polltemperature:
                    progress['platformtemperature'] = platformtemperature
                    progress['toolheadtemperature'] = toolheadtemperature
                task.heartbeat(progress)

    def _openserial(self):
        serialfp = serial.Serial(self._device, self._baudrate, timeout=0.1)

        # begin baud rate hack
        #
        # There is an interaction between the 8U2 firmware and
        # PySerial where PySerial thinks the 8U2 is already running
        # at the specified baud rate and it doesn't actually issue
        # the ioctl calls to set the baud rate. We work around it
        # by setting the baud rate twice, to two different values.
        # This forces PySerial to issue the correct ioctl calls.
        serialfp.baudrate = 9600
        serialfp.baudrate = self._baudrate
        # end baud rate hack

        return serialfp

    def print(self, gcodepath, skip_start_end=False):
        self._log.debug('gcodepath=%r', gcodepath)
        def runningcallback(task):
            try:
                with self._openserial() as serialfp:
                    writer = s3g.Writer.StreamWriter(serialfp)
                    self._genericprint(task, writer, True, gcodepath, skip_start_end)
            except Exception as e:
                self._log.exception('unhandled exception')
                task.fail(e)
            else:
                task.end(None)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task

    def printtofile(self, gcodepath, s3gpath, skip_start_end=False):
        self._log.debug('gcodepath=%r', gcodepath)
        def runningcallback(task):
            try:
                with open(s3gpath, 'w') as s3gfp:
                    writer = s3g.Writer.FileWriter(s3gfp)
                    self._genericprint(task, writer, False, gcodepath, skip_start_end)
            except Exception as e:
                self._log.exception('unhandled exception')
                task.fail(e)
            else:
                task.end(None)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task
