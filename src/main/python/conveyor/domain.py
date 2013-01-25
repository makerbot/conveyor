# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/domain.py
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

# NOTE: this file should go away.

import conveyor.enum

class DomainObject(object):
    def todict(self):
        raise NotImplementedError

    def to_dict(self):
        result = self.todict()
        return result


class Job(DomainObject):
    def __init__(
        self, id, build_name, path, config, printerid, gcodeprocessor,
        skip_start_end, with_start_end, slicer_settings, print_to_file_type, material):
            self.build_name = build_name
            self.conclusion = None
            self.currentstep = None
            self.failure = None
            self.id = id
            self.material = material
            self.path = path
            self.gcodeprocessor = gcodeprocessor
            self.printerid = printerid
            self.process = None
            self.skip_start_end = skip_start_end
            self.slicer_settings = slicer_settings
            self.state = "RUNNING"
            self.with_start_end = with_start_end
            self.print_to_file_type = print_to_file_type

    # TODO: we are not handling the currentstep and process fields evenly
    # between todict() and fromdict().
    #
    # TODO: and state and conclusion.

    def todict(self):
        dct = {
            'build_name': self.build_name,
            'conclusion': self.conclusion,
            'currentstep': self.currentstep, # TODO: not quite right
            'failure': self.failure, # TODO: also not quite right
            'id': self.id,
            'material': self.material,
            'name': self.build_name, # TODO: arrgh purge this
            'path': self.path,
            'gcodeprocessor': self.gcodeprocessor,
            'printerid': self.printerid,
            # TODO: process
            'skip_start_end': self.skip_start_end,
            'slicer_settings': self.slicer_settings.todict(),
            'state': self.state,
            'with_start_end': self.with_start_end,
            'print_to_file_type': self.print_to_file_type
        }
        return dct

    # TODO: fix all of this @*$!*$!%*!%!%&.

    @staticmethod
    def fromdict(dct):
        slicer_settings = SlicerConfiguration.fromdict(dct['slicer_settings'])
        job = Job(
            dct['id'], dct['build_name'], dct['path'], None,
            dct['printerid'], dct['gcodeprocessor'], dct['skip_start_end'],
            dct['with_start_end'],  slicer_settings, dct['print_to_file_type'], dct['material'])
        job.state = dct['state'] # TODO: :(
        job.conclusion = dct['conclusion'] # TODO: :'(
        job.failure = dct['failure'] # TODO: :''(
        return job

class Printer(DomainObject):
    def __init__(
        self, display_name, unique_name, printer_type, machine_names, can_print,
        can_printtofile, has_heated_platform, number_of_toolheads,
        connection_status, temperature, firmware_version):
            self.display_name = display_name
            self.unique_name = unique_name
            self.printer_type = printer_type
            self.machine_names = machine_names
            self.can_print = can_print
            self.can_printtofile = can_printtofile
            self.has_heated_platform = has_heated_platform
            self.number_of_toolheads = number_of_toolheads
            self.connection_status = connection_status
            self.temperature = temperature
            self.firmware_version = firmware_version

    def todict(self):
        dct = {
            'displayName': self.display_name,
            'uniqueName': self.unique_name,
            'printerType': self.printer_type,
            'machineNames' : self.machine_names,
            'canPrint': self.can_print,
            'canPrintToFile': self.can_printtofile,
            'hasHeatedPlatform': self.has_heated_platform,
            'numberOfToolheads': self.number_of_toolheads,
            'connectionStatus': self.connection_status,
            'temperature': self.temperature,
            'firmware_version': self.firmware_version,
        }
        return dct

    @staticmethod
    def fromdict(dct):
        printer = Printer(
            dct['displayName'], dct['uniqueName'], dct['printerType'],
            dct['machineNames'], dct['canPrint'], dct['canPrintToFile'], 
            dct['hasHeatedPlatform'], dct['numberOfToolheads'], 
            dct['connectionStatus'], dct['temperature'], dct['firmware_version'])
        return printer

    @staticmethod
    def fromprofile(profile, printerid, temperature, firmware_version):
        printer = Printer(
            display_name=profile.values['type'],
            unique_name=printerid,
            printer_type=profile.values['type'],
            machine_names=profile.values['machinenames'],
            can_print=True,
            can_printtofile=True,
            has_heated_platform=len(profile.values['heated_platforms']) != 0,
            number_of_toolheads=len(profile.values['tools']),
            connection_status='connected',
            temperature=temperature,
            firmware_version=firmware_version)
        return printer

Slicer = conveyor.enum.enum('Slicer', 'MIRACLEGRUE', 'SKEINFORGE')

class SlicerConfiguration(DomainObject):
    def __init__(
        self, slicer, extruder, raft, support, infill, layer_height, shells,
        extruder_temperature, platform_temperature, print_speed,
        travel_speed, path=None):
            self.slicer = slicer
            self.extruder = extruder
            self.raft = raft
            self.support = support
            self.infill = infill
            self.layer_height = layer_height
            self.shells = shells
            self.extruder_temperature = extruder_temperature
            self.platform_temperature = platform_temperature
            self.print_speed = print_speed
            self.travel_speed = travel_speed
            self.path = path

    def todict(self):
        dct = {
            'slicer': self.slicer,
            'extruder': self.extruder,
            'raft': self.raft,
            'support': self.support,
            'infill': self.infill,
            'layer_height': self.layer_height,
            'shells': self.shells,
            'extruder_temperature': self.extruder_temperature,
            'platform_temperature': self.platform_temperature,
            'print_speed': self.print_speed,
            'travel_speed': self.travel_speed,
            'path': self.path
        }
        return dct

    @staticmethod
    def fromdict(dct):
        slicerconfiguration = SlicerConfiguration(
            dct['slicer'], dct['extruder'], dct['raft'], dct['support'],
            dct['infill'], dct['layer_height'], dct['shells'],
            dct['extruder_temperature'], dct['platform_temperature'],
            dct['print_speed'], dct['travel_speed'], dct['path'])
        return slicerconfiguration
