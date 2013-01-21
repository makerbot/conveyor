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

import conveyor.enum
import conveyor.error
import conveyor.event
import conveyor.stoppable


class DriverManager(object):
    @staticmethod
    def create(config):
        driver_manager = DriverManager()

        import conveyor.machine.s3g
        profile_dir = config.get('makerbot_driver', 'profile_dir')
        driver = conveyor.machine.s3g.S3gDriver.create(profile_dir)
        driver_manager._drivers[driver.name] = driver

        # Add more drivers here.

        return driver_manager

    def __init__(self):
        self._drivers = {}

    def get_drivers(self):
        return self._drivers.values()

    def get_driver(self, driver_name):
        try:
            driver = self._drivers[driver_name]
        except KeyError:
            raise conveyor.error.UnknownDriverError(driver_name)
        else:
            return driver


class Driver(object):
    def __init__(self, name):
        self.name = name
        self._log = logging.getLogger(self.__class__.__name__)

    def get_profiles(self, port):
        raise NotImplementedError

    def get_profile(self, profile_name):
        raise NotImplementedError

    def new_machine_from_port(self, port, profile):
        raise NotImplementedError

    def print_to_file(
            self, profile, input_path, output_path, skip_start_end,
            extruders, extruder_temperature, platform_temperature,
            material_name, build_name, task):
        raise NotImplementedError


class Profile(object):
    def __init__(self, name, driver, xsize, ysize, zsize, can_print,
            can_print_to_file, has_heated_platform, number_of_tools):
        self.name = name
        self.driver = driver
        self.xsize = xsize
        self.ysize = ysize
        self.zsize = zsize
        self.can_print = can_print
        self.can_print_to_file = can_print_to_file
        self.has_heated_platform = has_heated_platform
        self.number_of_tools = number_of_tools

    def get_gcode_scaffold(
            self, extruders, extruder_temperature, platform_temperature,
            material_name):
        raise NotImplementedError


class GcodeScaffold(object):
    def __init__(self):
        self.start = None
        self.end = None
        self.variables = None


MachineState = conveyor.enum.enum(
    'MachineState', 'DISCONNECTED', 'BUSY', 'IDLE', 'OPERATION', 'PAUSED',)


MachineEvent = conveyor.enum.enum(
    'MachineEvent', 'CONNECT', 'DISCONNECT', 'DISCONNECTED', 'WENT_IDLE',
    'WENT_BUSY', 'START_OPERATION', 'PAUSE_OPERATION', 'UNPAUSE_OPERATION',
    'OPERATION_STOPPED',)


class MachineManager(object):
    def __init__(self):
        self._machines = {}

    def get_machines(self):
        machines = self._machines.values()
        return machines

    def get_machine(self, machine_id):
        try:
            machine = self._machines[machine_id]
        except KeyError:
            raise conveyor.error.UnknownMachineError(machine_id)
        else:
            return machine

    def new_machine(self, port, driver, profile):
        machine = driver.new_machine_from_port(port, profile)
        self._machines[machine.id] = machine
        return machine


class Machine(object):
    def __init__(self, id, driver, profile):
        self.id = id
        self._driver = driver
        self._profile = profile
        self._log = logging.getLogger(self.__class__.__name__)
        self._port = None
        self._state = MachineState.DISCONNECTED
        self._state_condition = threading.Condition()
        self.state_changed = conveyor.event.Event('state_changed')
        self.temperature_changed = conveyor.event.Event('temperature_changed')

    def get_port(self):
        return self._port

    def set_port(self, port):
        self._port = port

    def get_driver(self):
        return self._driver

    def get_profile(self):
        return self._profile

    def get_state(self):
        return self._state

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def pause(self):
        raise NotImplementedError

    def unpause(self):
        raise NotImplementedError

    def cancel(self):
        raise NotImplementedError

    def print(
            self, input_path, skip_start_end, extruders,
            extruder_temperature, platform_temperature, material_name,
            build_name, task):
        raise NotImplementedError

    def to_dict(self):
        dct = {
            'id': self.id,
            'state': self._state,
        }
        return dct
