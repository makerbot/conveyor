# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/machine/port/serial.py
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
import serial
import threading

import conveyor.log
import conveyor.machine.port


class SerialPortFactory(conveyor.machine.port.PortFactory):
    def __init__(self, driver_manager):
        conveyor.machine.port.PortFactory.__init__(self, driver_manager)
        self._thread = None

    def _start(self):
        self._thread = _SerialDetectorThread(self._driver_manager, self)
        self._thread.start()


class SerialPortInfo(conveyor.machine.port.PortInfo):
    def __init__(self, name, driver_profiles, path, iserial, vid, pid, label):
        conveyor.machine.port.PortInfo.__init__(
            self, conveyor.machine.port.PortType.SERIAL, name,
            driver_profiles)
        self.path = path
        self.iserial = iserial
        self.vid = vid
        self.pid = pid
        self.label = label

    def to_dict(self):
        dct = conveyor.machine.port.PortInfo.to_dict(self)
        dct['path'] = self.path
        dct['iserial'] = self.iserial
        dct['vid'] = self.vid
        dct['pid'] = self.pid
        dct['label'] = self.label
        return dct


class SerialPort(conveyor.machine.port.Port):
    def __init__(self, name, path, iserial, vid, pid, label):
        conveyor.machine.port.Port.__init__(
            self, conveyor.machine.port.PortType.SERIAL, name)
        self.path = path
        self.iserial = iserial
        self.vid = vid
        self.pid = pid
        self.label = label

    def get_info(self):
        info = SerialPortInfo(
            self.name, self.driver_profiles, self.path, self.iserial,
            self.vid, self.pid, self.label)
        return info

    def get_machine_name(self):
        vid = '%04X' % (self.vid,)
        pid = '%04X' % (self.pid,)
        machine_name = ':'.join((vid, pid, self.iserial))
        return machine_name

    def __str__(self):
        machine_name = self.get_machine_name()
        s = '%s, %s' % (self.name, machine_name)
        return s


class _SerialPortCategory(object):
    def __init__(self, vid, pid, label, *driver_names):
        self.vid = vid
        self.pid = pid
        self.label = label
        self.driver_names = driver_names


_SERIAL_PORT_CATEGORIES = [
    _SerialPortCategory(0x0103, 0x1771, 'FTDI',         's3g',),
    _SerialPortCategory(0x2341, 0x0010, 'Arduino Mega', 's3g',),
    _SerialPortCategory(0x23C1, 0xD314, 'Replicator',   's3g',),
    _SerialPortCategory(0x23C1, 0xB015, 'Replicator 2', 's3g',),
]


class _SerialDetectorThread(conveyor.stoppable.StoppableThread):
    def __init__(self, driver_manager, factory):
        conveyor.stoppable.StoppableThread.__init__(self)
        self._driver_manager = driver_manager
        self._factory = factory
        self._interval = 5.0
        self._log = conveyor.log.getlogger(self)
        self._prev_ports = {}
        self._prev_ports_condition = threading.Condition()
        self._stop = False
        self._stop_condition = threading.Condition()

    def run(self):
        try:
            while not self._stop:
                self._runiteration()
                with self._stop_condition:
                    self._stop_condition.wait(self._interval)
        except:
            self._log.exception('unhandled exception; serial port detection has stopped')

    def stop(self):
        self._stop = True
        with self._stop_condition:
            self._stop_condition.notify_all()

    def _runiteration(self):
        curr_ports = {}
        for dct in serial.tools.list_ports.list_ports_by_vid_pid():
            if self._is_usb(dct):
                serial_port_category = self._find_serial_port_category(dct)
                if None is not serial_port_category:
                    name = path = dct['port']
                    port = SerialPort(
                        name, path, dct['iSerial'], dct['VID'], dct['PID'],
                        serial_port_category.label)
                    for driver_name in serial_port_category.driver_names:
                        driver = self._driver_manager.get_driver(driver_name)
                        profiles = driver.get_profiles(port)
                        port.driver_profiles[driver_name] = [p.name for p in profiles]
                    curr_ports[name] = port
        with self._prev_ports_condition:
            prev_keys = set(self._prev_ports.keys())
            curr_keys = set(curr_ports.keys())
            detached_keys = prev_keys - curr_keys
            attached_keys = curr_keys - prev_keys
            self._prev_ports = curr_ports
        for port_name in detached_keys:
            self._factory.port_detached(port_name)
        for port_name in attached_keys:
            port = curr_ports[port_name]
            self._factory.port_attached(port)

    def _is_usb(self, dct):
        result = 'VID' in dct and 'PID' in dct and 'iSerial' in dct
        return result

    def _find_serial_port_category(self, dct):
        for serial_port_category in _SERIAL_PORT_CATEGORIES:
            if (dct['VID'] == serial_port_category.vid
                    and dct['PID'] == serial_port_category.pid):
                return serial_port_category
        return None
