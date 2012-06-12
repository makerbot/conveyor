# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/printer/replicator.py
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

class ReplicatorPrinter(object):
    def __init__(self, device='/dev/ttyACM0', baudrate=115200):
        self._baudrate = baudrate
        self._device = device
        self._log = logging.getLogger(self.__class__.__name__)
        self._pollinterval = 5.0

    def _countlines(self, gcodepath):
        with open(gcodepath, 'r') as gcodefp:
            i = 0
            for line in gcodefp:
                i += 1
            return i

    def print(self, gcodepath):
        self._log.debug('gcodepath=%r', gcodepath)
        def runningcallback(task):
            try:
                totallines = self._countlines(gcodepath)
                totalbytes = os.path.getsize(gcodepath)
                with serial.Serial(self._device, self._baudrate, timeout=0) as serialfp:
                    parser = s3g.Gcode.GcodeParser()
                    parser.state.SetBuildName(str('xyzzy'))
                    parser.s3g = s3g.s3g()
                    parser.s3g.writer = s3g.Writer.StreamWriter(serialfp)
                    polltime = time.time()
                    with open(gcodepath) as gcodefp:
                        for currentline, data in enumerate(gcodefp):
                            currentbyte = gcodefp.tell()
                            now = time.time()
                            if polltime <= now:
                                toolheadtemperature = parser.s3g.GetToolheadTemperature(0)
                                platformtemperature = parser.s3g.GetPlatformTemperature(0)
                                self._log.info('toolhead temperature: %r', toolheadtemperature)
                                self._log.info('platform temperature: %r', platformtemperature)
                                polltime = now + self._pollinterval
                            self._log.info('gcode: %s', data.strip())
                            parser.ExecuteLine(data)
                            task.heartbeat((currentline, totallines, currentbyte, totalbytes))
            except Exception as e:
                self._log.exception('unhandled exception')
                task.fail(e)
            else:
                task.end(None)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task

    def printtofile(self, gcodepath, s3gpath):
        self._log.debug('gcodepath=%r', gcodepath)
        def runningcallback(task):
            try:
                totallines = self._countlines(gcodepath)
                totalbytes = os.path.getsize(gcodepath)
                with open(s3gpath, 'w') as s3gfp:
                    parser = s3g.Gcode.GcodeParser()
                    parser.state.SetBuildName(str('xyzzy'))
                    parser.s3g = s3g.s3g()
                    parser.s3g.writer = s3g.Writer.FileWriter(s3gfp)
                    with open(gcodepath) as gcodefp:
                        for currentline, data in enumerate(gcodefp):
                            currentbyte = gcodefp.tell()
                            self._log.info('gcode: %s', data.strip())
                            parser.ExecuteLine(data)
                            task.heartbeat((currentline, totallines, currentbyte, totalbytes))
            except Exception as e:
                self._log.exception('unhandled exception')
                task.fail(e)
            else:
                task.end(None)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task
