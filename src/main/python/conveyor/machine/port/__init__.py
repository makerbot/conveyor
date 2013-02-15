# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/machine/port/__init__.py
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

import conveyor.enum
import conveyor.error
import conveyor.event
import conveyor.log


class PortManager(object):
    @staticmethod
    def create(driver_manager):
        portmanager = PortManager(driver_manager)

        import conveyor.machine.port.serial
        portmanager._factories.append(
            conveyor.machine.port.serial.SerialPortFactory(driver_manager))

        # Add more port factories here.

        portmanager._start()
        return portmanager

    def __init__(self, driver_manager):
        self._driver_manager = driver_manager
        self._factories = []
        self._ports = {}
        self.port_attached = conveyor.event.Event('port_attached')
        self.port_attached.attach(self._handle_port_attached)
        self.port_detached = conveyor.event.Event('port_detached')
        self.port_detached.attach(self._handle_port_detached)

    def get_ports(self):
        ports = self._ports.values()
        return ports

    def get_port(self, port_name):
        try:
            port = self._ports[port_name]
        except KeyError:
            raise conveyor.error.UnknownPortError(port_name)
        else:
            return port

    def _start(self):
        for factory in self._factories:
            factory.port_attached.attach(self.port_attached)
            factory.port_detached.attach(self.port_detached)
            factory._start()

    def _handle_port_attached(self, port):
        self._ports[port.name] = port

    def _handle_port_detached(self, port_name):
        del self._ports[port_name]


class PortFactory(object):
    def __init__(self, driver_manager):
        self._driver_manager = driver_manager
        self._log = conveyor.log.getlogger(self)
        self.port_attached = conveyor.event.Event('port_attached')
        self.port_attached.attach(self._port_attached_callback)
        self.port_detached = conveyor.event.Event('port_detached')
        self.port_detached.attach(self._port_detached_callback)

    def _start(self):
        raise NotImplementedError

    def _port_attached_callback(self, port):
        self._log.info('port attached: %s', port)

    def _port_detached_callback(self, port_name):
        self._log.info('port detached: %s', port_name)


PortType = conveyor.enum.enum('PortType', 'SERIAL')


class PortInfo(object):
    def __init__(self, type_, name, driver_profiles):
        self.type = type_
        self.name = name
        self.driver_profiles = driver_profiles

    def to_dict(self):
        dct = {
            'type': self.type,
            'name': self.name,
            'driver_profiles': self.driver_profiles,
        }
        return dct


class Port(object):
    def __init__(self, type, name):
        self.type = type
        self.name = name
        self.driver_profiles = {}
        self._machine = None

    def get_info(self):
        raise NotImplementedError

    def get_machine_name(self):
        '''
        Get the name of the machine associated with this port. The actual
        machine may not be connected and it may not be set to this port (i.e.,
        the port's `get_machine` method may return `None`). This method may
        return `None` if the port is unable to determine the machine's name.

        '''

        raise NotImplementedError

    def has_machine_name(self, machine_name):
        '''
        Return whether or not the port is associated with the specified machine
        name. The actual machine may not be connected and it may not be set to
        this port (i.e., the port's `get_machine` method may return `None`).

        '''

        result = (self.get_machine_name() == machine_name)
        return result

    def get_machine(self):
        return self._machine

    def set_machine(self, machine):
        self._machine = machine
