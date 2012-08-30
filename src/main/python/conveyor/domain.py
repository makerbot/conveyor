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

# NOTE: If you convert it to or from JSON, it should go in this file.

class DomainObject(object):
    def todict(self):
        raise NotImplementedError

class Job(DomainObject):
    def __init__(
        self, id, build_name, path, config, preprocessor, skip_start_end,
        with_start_end):
            self.build_name = build_name
            self.config = config
            self.id = id
            self.path = path
            self.preprocessor = preprocessor
            self.process = None
            self.skip_start_end = skip_start_end
            self.with_start_end = with_start_end

    def todict(self):
        dct = {
            'id': self.id,
            'build_name': self.build_name,
            'config': self.config,
            'path': self.path,
            'preprocessor': self.preprocessor,
            'skip_start_end': self.skip_start_end,
            'with_start_end': self.with_start_end
        }
        return dct

    @staticmethod
    def fromdict(dct):
        job = Job(
            dct['id'], dct['build_name'], dct['path'], dct['config'],
            dct['preprocessor'], dct['skip_start_end'], dct['with_start_end'])
        return job

class Printer(DomainObject):
    def __init__(
        self, display_name, unique_name, printer_type, can_print,
        can_printtofile, has_heated_platform, number_of_toolheads,
        connection_status, temperature):
            self.display_name = display_name
            self.unique_name = unique_name
            self.printer_type = printer_type
            self.can_print = can_print
            self.can_printtofile = can_printtofile
            self.has_heated_platform = has_heated_platform
            self.number_of_toolheads = number_of_toolheads
            self.connection_status = connection_status
            self.temperature = temperature

    def todict(self):
        dct = {
            'displayName': self.display_name,
            'uniqueName': self.unique_name,
            'printerType': self.printer_type,
            'canPrint': self.can_print,
            'canPrintToFile': self.can_printtofile,
            'hasHeatedPlatform': self.has_heated_platform,
            'numberOfToolheads': self.number_of_toolheads,
            'connectionStatus': self.connection_status,
            'temperature': self.temperature
        }
        return dct

    @staticmethod
    def fromdict(dct):
        printer = Printer(
            dct['displayName'], dct['uniqueName'], dct['printerType'],
            dct['canPrint'], dct['canPrintToFile'], dct['hasHeatedPlatform'],
            dct['numberOfToolheads'], dct['connectionStatus'],
            dct['temperature'])
        return printer

    @staticmethod
    def fromprofile(profile, printerid, temperature):
        printer = Printer(
            display_name=profile.values['type'],
            unique_name=printerid,
            printer_type=profile.values['type'],
            can_print=True,
            can_printtofile=True,
            has_heated_platform=len(profile.values['heated_platforms']) != 0,
            number_of_toolheads=len(profile.values['tools']),
            connection_status='connected',
            temperature=temperature)
        return printer
