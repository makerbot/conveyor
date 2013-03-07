# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/spool.py
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
import threading

import conveyor.log
import conveyor.machine


class Spool(object):
    def __init__(self):
        self._machine_spools = {}
        self._machine_spools_condition = threading.Condition()

    def is_spool_empty(self, machine):
        machine_spool = self._get_machine_spool(machine)
        empty = machine_spool.is_spool_empty()
        return empty

    def spool_print(
            self, machine, input_path, extruders, extruder_temperature,
            platform_temperature, material_name, build_name, task):
        machine_spool = self._get_machine_spool(machine)
        machine_spool.spool_print(
            input_path, extruders, extruder_temperature, platform_temperature,
            material_name, build_name, task)

    def _get_machine_spool(self, machine):
        with self._machine_spools_condition:
            if machine.name in self._machine_spools:
                machine_spool = self._machine_spools[machine.name]
            else:
                machine_spool = _MachineSpool.create(machine)
                self._machine_spools[machine.name] = machine_spool
            return machine_spool


class _MachineSpool(object):
    @staticmethod
    def create(machine):
        machine_spool = _MachineSpool(machine)
        machine.state_changed.attach(machine_spool._state_changed_callback)
        return machine_spool

    def __init__(self, machine):
        self._machine = machine
        self._log = conveyor.log.getlogger(self)
        self._spool = collections.deque()
        self._spool_condition = threading.Condition()

    def is_spool_empty(self):
        with self._spool_condition:
            empty = 0 == len(self._spool)
        return empty

    def spool_print(
            self, input_path, extruders, extruder_temperature,
            platform_temperature, material_name, build_name, task):
        tuple_ = (
            input_path, extruders, extruder_temperature, platform_temperature,
            material_name, build_name, task)
        with self._spool_condition:
            self._spool.append(tuple_)
        self._attempt_print()

    def _state_changed_callback(self, machine):
        self._attempt_print()

    def _attempt_print(self):
        if conveyor.machine.MachineState.IDLE == self._machine.get_state():
            with self._spool_condition:
                if 0 != len(self._spool):
                    tuple_ = self._spool[0]
                    try:
                        self._machine.print(*tuple_)
                    except Exception:
                        self._log.debug('handled exception', exc_info=True)
                    else:
                        self._spool.popleft()
