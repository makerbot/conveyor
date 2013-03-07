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
            self, type_, id_, name, state, progress, conclusion, failure,
            machine_name, port_name, driver_name, profile_name):
        self.type = type_
        self.id = id_
        self.name = name
        self.state = state
        self.progress = progress
        self.conclusion = conclusion
        self.failure = failure
        self.machine_name = machine_name
        self.port_name = port_name
        self.driver_name = driver_name
        self.profile_name = profile_name

    def to_dict(self):
        dct = {
            'type': self.type,
            'id': self.id,
            'name': self.name,
            'state': self.state,
            'progress': self.progress,
            'conclusion': self.conclusion,
            'failure': self.failure,
            'machine_name': self.machine_name,
            'port_name': self.port_name,
            'driver_name': self.driver_name,
            'profile_name': self.profile_name,
        }
        return dct

    @staticmethod
    def from_dict(dct):
        info = JobInfo(
            dct['type'], dct['id'], dct['name'], dct['state'],
            dct['progress'], dct['conclusion'], dct['failure'],
            dct['machine_name'], dct['port_name'], dct['driver_name'],
            dct['profile_name'])
        return info


class Job(object):
    def __init__(self, type_, id_, name):
        self.type = type_
        self.id = id_
        self.name = name
        self.task = None

    def _get_machine_name(self):
        return None

    def _get_port_name(self):
        return None

    def _get_driver_name(self):
        return None

    def _get_profile_name(self):
        return None

    def _get_state(self):
        if None is self.task:
            state = None
        else:
            state = self.task.state
        return state

    def _get_progress(self):
        if None is self.task:
            progress = None
        else:
            child_task = self.task.progress
            if None is child_task:
                progress = None
            else:
                progress = child_task.progress
        return progress

    def _get_failure(self):
        if None is self.task:
            failure = None
        else:
            child_task = self.task.failure
            if None is child_task:
                failure = None
            else:
                failure = child_task.failure
        return failure

    def _get_conclusion(self):
        if None is self.task:
            conclusion = None
        else:
            conclusion = self.task.conclusion
        return conclusion

    def get_info(self):
        state = self._get_state()
        progress = self._get_progress()
        failure = self._get_failure()
        conclusion = self._get_conclusion()
        machine_name = self._get_machine_name()
        port_name = self._get_port_name()
        driver_name = self._get_driver_name()
        profile_name = self._get_profile_name()
        info = JobInfo(
            self.type, self.id, self.name, state, progress, conclusion,
            failure, machine_name, port_name, driver_name, profile_name)
        return info

    def log_job_started(self, log):
        raise NotImplementedError

    def log_job_heartbeat(self, log):
        progress = self._get_progress()
        if None is not progress:
            log.info(
                'job %d: progress: %s, %d%%', self.id, progress['name'],
                progress['progress'])

    def log_job_stopped(self, log):
        conclusion = self._get_conclusion()
        if conveyor.task.TaskConclusion.ENDED == conclusion:
            log.info('job %d: ended', self.id)
        elif conveyor.task.TaskConclusion.FAILED == conclusion:
            failure = self._get_failure()
            log.error('job %d: failed: %r', self.id, failure)
        elif conveyor.task.TaskConclusion.CANCELED == conclusion:
            log.warning('job %d: canceled', self.id)
        else:
            raise ValueError(conclusion)


class RecipeJob(Job):
    def get_has_start_end(self):
        raise NotImplementedError

    def get_add_start_end(self):
        raise NotImplementedError

    def get_profile(self):
        raise NotImplementedError


class PrintJob(RecipeJob):
    def __init__(
            self, id, name, machine, input_file, extruder_name,
            gcode_processor_names, has_start_end, material_name, slicer_name,
            slicer_settings):
        Job.__init__(self, JobType.PRINT_JOB, id, name)
        self.machine = machine
        self.input_file = input_file
        self.extruder_name = extruder_name
        self.gcode_processor_names = gcode_processor_names
        self.has_start_end = has_start_end
        self.material_name = material_name
        self.slicer_name = slicer_name
        self.slicer_settings = slicer_settings

    def _get_machine_name(self):
        return self.machine.name

    def _get_port_name(self):
        # NOTE: a machine may be disconnected and it will not have a port. I'm
        # not sure how a print job would get sent to a disconnected machine (at
        # least not in this version), but we check the port against `None`
        # anyway.
        port = self.machine.get_port()
        if None is port:
            port_name = None
        else:
            port_name = port.name
        return port_name

    def _get_driver_name(self):
        driver = self.machine.get_driver()
        return driver.name

    def _get_profile_name(self):
        profile = self.machine.get_profile()
        return profile.name

    def log_job_started(self, log):
        log.info(
            'job %d: started printing: %s -> %s', self.id, self.input_file,
            self.machine.name)

    def get_has_start_end(self):
        return self.has_start_end

    def get_add_start_end(self):
        return True

    def get_profile(self):
        profile = self.machine.get_profile()
        return profile


class PrintToFileJob(RecipeJob):
    def __init__(
            self, id, name, driver, profile, input_file, output_file,
            extruder_name, file_type, gcode_processor_names, has_start_end,
            material_name, slicer_name, slicer_settings):
        Job.__init__(self, JobType.PRINT_TO_FILE_JOB, id, name)
        self.driver = driver
        self.profile = profile
        self.input_file = input_file
        self.output_file = output_file
        self.extruder_name = extruder_name
        self.file_type = file_type
        self.gcode_processor_names = gcode_processor_names
        self.has_start_end = has_start_end
        self.material_name = material_name
        self.slicer_name = slicer_name
        self.slicer_settings = slicer_settings

    def _get_driver_name(self):
        return self.driver.name

    def _get_profile_name(self):
        return self.profile.name

    def log_job_started(self, log):
        log.info(
            'job %d: started print-to-file: %s -> %s', self.id,
            self.input_file, self.output_file)

    def get_has_start_end(self):
        return self.has_start_end

    def get_add_start_end(self):
        return True

    def get_profile(self):
        return self.profile


class SliceJob(RecipeJob):
    def __init__(
            self, id, name, driver, profile, input_file, output_file,
            add_start_end, extruder_name, gcode_processor_names,
            material_name, slicer_name, slicer_settings):
        Job.__init__(self, JobType.SLICE_JOB, id, name)
        self.driver = driver
        self.profile = profile
        self.input_file = input_file
        self.output_file = output_file
        self.add_start_end = add_start_end
        self.extruder_name = extruder_name
        self.gcode_processor_names = gcode_processor_names
        self.material_name = material_name
        self.slicer_name = slicer_name
        self.slicer_settings = slicer_settings

    def _get_driver_name(self):
        return self.driver.name

    def _get_profile_name(self):
        return self.profile.name

    def log_job_started(self, log):
        log.info(
            'job %d: started slicing: %s -> %s', self.id, self.input_file,
            self.output_file)

    def get_has_start_end(self):
        return False

    def get_add_start_end(self):
        return self.add_start_end

    def get_profile(self):
        return self.profile
