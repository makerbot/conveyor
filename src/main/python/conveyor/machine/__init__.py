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
import conveyor.log
import conveyor.stoppable


class DriverManager(object):
    @staticmethod
    def create(config):
        driver_manager = DriverManager()

        import conveyor.machine.s3g
        profile_dir = config.get('makerbot_driver', 'profile_dir')
        driver = conveyor.machine.s3g.S3gDriver.create(config, profile_dir)
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


class DriverInfo(object):
    def __init__(self, name, profiles):
        self.name = name
        self.profiles = profiles

    def to_dict(self):
        dct = {
            'name': self.name,
            'profiles': [p.to_dict() for p in self.profiles],
        }
        return dct


class Driver(object):
    def __init__(self, name, config):
        self.name = name
        self._config = config
        self._log = conveyor.log.getlogger(self)

    def get_profiles(self, port):
        raise NotImplementedError

    def get_profile(self, profile_name):
        raise NotImplementedError

    def new_machine_from_port(self, port, profile):
        raise NotImplementedError

    def print_to_file(
            self, profile, input_file, output_file, file_type, has_start_end,
            extruders, extruder_temperature, platform_temperature,
            material_name, build_name, task):
        raise NotImplementedError

    def get_info(self):
        profiles = []
        for profile in self.get_profiles(None):
            profile_info = profile.get_info()
            profiles.append(profile_info)
        info = DriverInfo(self.name, profiles)
        return info

    # TODO: these are specific to S3G.

    def get_uploadable_machines(self, task):
        raise NotImplementedError

    def get_machine_versions(self, machine_type, task):
        raise NotImplementedError

    def compatible_firmware(self, firmware_version):
        raise NotImplementedError

    def download_firmware(self, machine_type, firmware_version, task):
        raise NotImplementedError


class ProfileInfo(object):
    '''This is the JSON-serializable portion of a `Profile`.'''

    def __init__(
            self, name, driver_name, xsize, ysize, zsize, can_print,
            can_print_to_file, has_heated_platform, number_of_tools):
        self.name = name
        self.driver_name = driver_name
        self.xsize = xsize
        self.ysize = ysize
        self.zsize = zsize
        self.can_print = can_print
        self.can_print_to_file = can_print_to_file
        self.has_heated_platform = has_heated_platform
        self.number_of_tools = number_of_tools

    def to_dict(self):
        dct = {
            'name': self.name,
            'driver_name': self.driver_name,
            'xsize': self.xsize,
            'ysize': self.ysize,
            'zsize': self.zsize,
            'can_print': self.can_print,
            'can_print_to_file': self.can_print_to_file,
            'has_heated_platform': self.has_heated_platform,
            'number_of_tools': self.number_of_tools,
        }
        return dct


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

    def get_info(self):
        info = ProfileInfo(
            self.name, self.driver.name, self.xsize, self.ysize, self.zsize,
            self.can_print, self.can_print_to_file, self.has_heated_platform,
            self.number_of_tools,)
        return info


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
        self._log = conveyor.log.getlogger(self)
        self._machines = {}

    def get_machines(self):
        machines = self._machines.values()
        return machines

    def get_machine(self, machine_name):
        try:
            machine = self._machines[machine_name]
        except KeyError:
            raise conveyor.error.UnknownMachineError(machine_name)
        else:
            return machine

    def new_machine(self, port, driver, profile):
        machine = driver.new_machine_from_port(port, profile)
        machine.set_port(port)
        port.set_machine(machine)
        machine_port = machine.get_port()
        machine_driver = machine.get_driver()
        machine_profile = machine.get_profile()
        self._log.info(
            'creating new machine: name=%s, port=%s, driver=%s, profile=%s',
            machine.name, machine_port.name, machine_driver.name,
            machine_profile.name)
        self._machines[machine.name] = machine
        return machine


class MachineInfo(object):
    '''This is the JSON-serializable portion of a `Machine`.'''

    def __init__(self, name, port_name, driver_name, profile_name, state):
        self.name = name
        self.port_name = port_name
        self.driver_name = driver_name
        self.profile_name = profile_name
        self.state = state

        # Below are the fields from the old `Printer` object. Not all of them
        # are useful. The `_S3gMachine` should populate these fields.
        #
        # We dropped the `connection_status` field since it had been
        # permanently set to `connected` and is now subsumed by `state`.

        self.display_name = None
        self.unique_name = None
        self.printer_type = None
        self.machine_names = None
        self.can_print = None
        self.can_printtofile = None
        self.has_heated_platform = None
        self.number_of_toolheads = None
        self.temperature = None
        self.firmware_version = None
        self.build_volume = None

    def to_dict(self):
        dct = {
            'name': self.name,
            'port_name': self.port_name,
            'driver_name': self.driver_name,
            'profile_name': self.profile_name,
            'state': self.state,

            # Old stuff:

            'displayName': self.display_name,
            'uniqueName': self.unique_name,
            'printerType': self.printer_type,
            'machineNames': self.machine_names,
            'canPrint': self.can_print,
            'canPrintToFile': self.can_printtofile,
            'hasHeatedPlatform': self.has_heated_platform,
            'numberOfToolheads': self.number_of_toolheads,
            'temperature': self.temperature,
            'firmware_version': self.firmware_version,
            'build_volume': self.build_volume,
        }
        return dct


class Machine(object):
    def __init__(self, name, driver, profile):
        self.name = name
        self._driver = driver
        self._profile = profile
        self._log = conveyor.log.getlogger(self)
        self._port = None
        self._state = MachineState.DISCONNECTED
        self._state_condition = threading.Condition()
        self.state_changed = conveyor.event.Event('state_changed')
        self.temperature_changed = conveyor.event.Event('temperature_changed')

    def get_info(self):
        raise NotImplementedError

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

    def is_idle(self):
        raise NotImplementedError

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
            self, input_path, extruders, extruder_temperature,
            platform_temperature, material_name, build_name, task):
        raise NotImplementedError

    # TODO: these are specific to S3G.

    def reset_to_factory(self, task):
        raise NotImplementedError

    def upload_firmware(self, machine_type, input_file, task):
        raise NotImplementedError

    def read_eeprom(self, task):
        raise NotImplementedError

    def write_eeprom(self, eeprom_map, task):
        raise NotImplementedError
