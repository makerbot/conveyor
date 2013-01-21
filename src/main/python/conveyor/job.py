# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/job.py
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

import conveyor.enum

# NOTE: the `from_dict` method is only present on `Job` and `NamedJob` because
# conveyor never needs to decode any other type of job from JSON.


JobType = conveyor.enum.enum(
    'JobType', 'PRINT_JOB', 'PRINT_TO_FILE_JOB', 'SLICE_JOB')


class Job(object):
    def __init__(self, type_, id):
        self.type = type_
        self.id = id
        self.state = conveyor.task.TaskState.PENDING
        self.progress = None
        self.conclusion = None
        self.failure = None

    def to_dict(self):
        dct = {
            'type': self.type_,
            'id': self.id,
            'state': self.state,
            'progress': self.progress,
            'conclusion': self.conclusion,
            'failure': self.failure,
        }
        return dct

    @staticmethod
    def from_dict(dct):
        job = Job(dct['type'], dct['id'])
        job.state = dct['state']
        job.progress = dct['progress']
        job.conclusion = dct['conclusion']
        job.failure = dct['failure']
        return job


class NamedJob(Job):
    def __init__(self, type_, id, name):
        Job.__init__(self, type, id)
        self.name = name

    def to_dict(self):
        dct = Job.to_dict(self)
        dct['name'] = name
        return dct

    @staticmethod
    def from_dict(dct):
        named_job = NamedJob(dct['type'], dct['id'], dct['name'])
        named_job.state = dct['state']
        named_job.progress = dct['progress']
        named_job.conclusion = dct['conclusion']
        named_job.failure = dct['failure']
        return named_job


class PrintJob(Job):
    def __init__(
            self, id, name, machine_name, port_name, driver_name,
            profile_name, input_file, extruder_name, gcode_processor_name,
            has_start_end, material_name, slicer_name, slicer_settings):
        Job.__init__(self, JobType.PRINT_JOB, id, name)
        self.machine_name = machine_name
        self.port_name = port_name
        self.driver_name = driver_name
        self.profile_name = profile_name
        self.input_file = input_file
        self.extruder_name = extruder_name
        self.gcode_processor_name = gcode_processor_name
        self.has_start_end = has_start_end
        self.material_name = material_name
        self.slicer_name = slicer_name
        self.slicer_settings = slicer_settings

    def to_dict(self):
        dct = Job.to_dict(self)
        dct['machine_name'] = self.machine_name
        dct['port_name'] = self.port_name
        dct['driver_name'] = self.driver_name
        dct['profile_name'] = self.profile_name
        dct['input_file'] = self.input_file
        dct['extruder_name'] = self.extruder_name
        dct['gcode_processor_name'] = self.gcode_processor_name
        dct['has_start_end'] = self.has_start_end
        dct['material_name'] = self.material_name
        dct['slicer_name'] = self.slicer_name
        dct['slicer_settings'] = self.slicer_settings
        return dct


class PrintToFileJob(NamedJob):
    def __init__(
            self, id, name, driver_name, profile_name, input_file,
            output_file, extruder_name, gcode_processor_name, has_start_end,
            material_name, slicer_name, slicer_settings):
        Job.__init__(self, JobType.PRINT_TO_FILE, id, name)
        self.driver_name = driver_name
        self.profile_name = profile_name
        self.input_file = input_file
        self.output_file = output_file
        self.extruder_name = extruder_name
        self.gcode_processor_name = gcode_processor_name
        self.has_start_end = has_start_end
        self.material_name = material_name
        self.slicer_name = slicer_name
        self.slicer_settings = slicer_settings

    def to_dict(self):
        dct = Job.to_dict(self)
        dct['driver_name'] = self.driver_name
        dct['profile_name'] = self.profile_name
        dct['input_file'] = self.input_file
        dct['output_file'] = self.output_file
        dct['extruder_name'] = self.extruder_name
        dct['gcode_processor_name'] = self.gcode_processor_name
        dct['has_start_end'] = self.has_start_end
        dct['material_name'] = self.material_name
        dct['slicer_name'] = self.slicer_name
        dct['slicer_settings'] = self.slicer_settings
        return dct


class SliceJob(Job):
    def __init__(
            self, id, name, driver_name, profile_name, input_file,
            output_file, add_start_end, extruder_name, gcode_processor_name,
            material_name, slicer_name, slicer_settings):
        Job.__init__(self, JobType.SLICE_JOB, id, name)
        self.driver_name = driver_name
        self.profile_name = profile_name
        self.input_file = input_file
        self.output_file = output_file
        self.add_start_end = add_start_end
        self.extruder_name = extruder_name
        self.gcode_processor_name = gcode_processor_name
        self.material_name = material_name
        self.slicer_name = slicer_name
        self.slicer_settings = slicer_settings

    def to_dict(self):
        dct = Job.to_dict(self)
        dct['driver_name'] = self.driver_name
        dct['profile_name'] = self.profile_name
        dct['input_file'] = self.input_file
        dct['output_file'] = self.output_file
        dct['add_start_end'] = self.add_start_end
        dct['extruder_name'] = self.extruder_name
        dct['gcode_processor_name'] = self.gcode_processor_name
        dct['material_name'] = self.material_name
        dct['slicer_name'] = self.slicer_name
        dct['slicer_settings'] = self.slicer_settings
        return dct
