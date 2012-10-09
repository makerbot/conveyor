# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/machine/__init__.py
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
import threading

import conveyor.event
import conveyor.stoppable

class MachineDriver(object):
    def __init__(self):
        self.portadded = conveyor.event.Event('portadded')
        self.portremoved = conveyor.event.Event('portremoved')

    def initialize(self):
        raise NotImplementedError

    def getport(self, port_name):
        raise NotImplementedError

    def getports(self):
        raise NotImplementedError

    def getprofile(self, profile_name):
        raise NotImplementedError

    def getprofiles(self):
        raise NotImplementedError

class MachinePort(object):
    def __init__(self):
        pass

    def getuid(self):
        raise NotImplementedError

    def connect(self, profile):
        raise NotImplementedError

    def isconnceted(self):
        raise NotImplementedError

class MachineProfile(object):
    def __init__(self):
        self.xsize = None
        self.ysize = None
        self.zsize = None

    def get_gcode_scaffold(self):
        raise NotImplementedError

    def make_file(self, job, path, task):
        raise NotImplementedError

class Machine(object):
    def __init__(self):
        self.port = None
        self.profile = None

    def disconnect(self):
        raise NotImplementedError

    def preheat(self, job, task):
        raise NotImplementedError

    def make(self, job, task):
        raise NotImplementedError

    def update_firmware(self, path, task):
        raise NotImplementedError

    def getsettings(self, task):
        raise NotImplementedError

    def setsettings(self, settings, task):
        raise NotImplementedError

    def home(self, task):
        raise NotImplementedError

    def move_relative(self, position, task):
        raise NotImplementedError

class GcodeScaffold(object):
    def __init__(self):
        self.start = None
        self.end = None
        self.variables = None

class SerialMachineDriver(MachineDriver):
    def __init__(self):
        MachineDriver.__init__(self)
        self._detectorthread = None
        self._log = logging.getLogger(self.__class__.__name__)
        self._ports = {}

    def initialize(self):
        if None is self._detectorthread:
            self._detectorthread = _SerialDetectorThread(self)
            self._detectorthread.start()

    def getport(self, port_name):
        port = self._ports[port_name]
        return port

    def getports(self):
        ports = self._ports.items()
        return ports

    def _addport(self, port_name, port):
        self._ports[port_name] = port
        self.portadded(port_name, port)

    def _removeport(self, port_name):
        del self._ports[port_name]
        self.portremoved(port_name)

class SerialMachinePort(MachinePort):
    def __init__(self):
        MachinePort.__init__(self)
        self.path = None
        self.vid = None
        self.pid = None
        self.iserial = None
        self.baudrate = None

class SerialMachineProfile(MachineProfile):
    def __init__(self):
        MachineProfile.__init__(self)

class SerialMachine(Machine):
    def __init__(self):
        Machine.__init__(self)

class _SerialDetectorThread(conveyor.stoppable.StoppableThread):
    def __init__(Self, driver):
        conveyor.stoppable.StoppableThread.__init__(self)
        self._condition = threading.Condition()
        self._driver = driver
        self._interval = 5.0
        self._log = logging.getLogger(self.__class__.__name__)
        self._stop = False

    def run(self):
        try:
            while not self._stop:
                self._runiteration()
                with self._condition:
                    self._condition.wait(self._interval)
        except:
            self._log.exception('unhandled exception', exc_info=True)

    def stop(self):
        self._stop = True
        with self._condition:
            self._condition.notify_all()

    def _runiteration(self):
        pass
