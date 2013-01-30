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


JobType = conveyor.enum.enum(
    'JobType', 'PRINT_JOB', 'PRINT_TO_FILE_JOB', 'SLICE_JOB')


class JobInfo(object):
    '''This is the JSON-serializable portion of a `Job`.'''

    def __init__(
            self, type_, id_, name, state, progress, conclusion, failure):
        self.type = type_
        self.id = id_
        self.name = name
        self.state = state
        self.progress = progress
        self.conclusion = conclusion
        self.failure = failure

    def to_dict(self):
        dct = {
            'type': self.type,
            'id': self.id,
            'name': self.name,
            'state': self.state,
            'progress': self.progress,
            'conclusion': self.conclusion,
            'failure': self.failure,
        }
        return dct

    @staticmethod
    def from_dict(dct):
        info = JobInfo(
            dct['type'], dct['id'], dct['name'], dct['state'],
            dct['progress'], dct['conclusion'], dct['failure'])
        return info


class Job(object):
    def __init__(self, type_, id_, name):
        self.type = type_
        self.id = id_
        self.name = name
        self.task = None

    def get_info(self):
        if None is self.task:
            state = None
            progress = None
            conclusion = None
            failure = None
        else:
            state = self.task.state
            child_task = self.task.progress
            if None is child_task:
                progress = None
                failure = None
            else:
                progress = child_task.progress
                failure = child_task.failure
            conclusion = self.task.conclusion
        info = JobInfo(
            self.type, self.id, self.name, state, progress, conclusion,
            failure)
        return info


class PrintJob(Job):
    def __init__(
            self, id, name, machine, input_file, extruder_name,
            gcode_processor_name, has_start_end, material_name, slicer_name,
            slicer_settings):
        Job.__init__(self, JobType.PRINT_JOB, id, name)
        self.machine = machine
        self.input_file = input_file
        self.extruder_name = extruder_name
        self.gcode_processor_name = gcode_processor_name
        self.has_start_end = has_start_end
        self.material_name = material_name
        self.slicer_name = slicer_name
        self.slicer_settings = slicer_settings


class PrintToFileJob(Job):
    def __init__(
            self, id, name, driver, profile, input_file, output_file,
            extruder_name, gcode_processor_name, has_start_end,
            material_name, slicer_name, slicer_settings):
        Job.__init__(self, JobType.PRINT_TO_FILE, id, name)
        self.driver = driver
        self.profile = profile
        self.input_file = input_file
        self.output_file = output_file
        self.extruder_name = extruder_name
        self.gcode_processor_name = gcode_processor_name
        self.has_start_end = has_start_end
        self.material_name = material_name
        self.slicer_name = slicer_name
        self.slicer_settings = slicer_settings


class SliceJob(Job):
    def __init__(
            self, id, name, driver, profile, input_file, output_file,
            add_start_end, extruder_name, gcode_processor_name,
            material_name, slicer_name, slicer_settings):
        Job.__init__(self, JobType.SLICE_JOB, id, name)
        self.driver = driver
        self.profile = profile
        self.input_file = input_file
        self.output_file = output_file
        self.add_start_end = add_start_end
        self.extruder_name = extruder_name
        self.gcode_processor_name = gcode_processor_name
        self.material_name = material_name
        self.slicer_name = slicer_name
        self.slicer_settings = slicer_settings
