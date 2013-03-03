# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/slicer/__init__.py
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

import cStringIO as StringIO
import logging
import os.path
import subprocess

import conveyor.log
import conveyor.task
import conveyor.util


class Slicer(object):
    MIRACLEGRUE = 'miraclegrue'

    SKEINFORGE = 'skeinforge'

    _name = None

    _display_name = None

    @staticmethod
    def get_gcode_scaffold(path):
        raise NotImplementedError

    def __init__(
            self, profile, input_file, output_file, slicer_settings, material,
            dualstrusion, task):
        self._log = conveyor.log.getlogger(self)
        self._profile = profile
        self._input_file = input_file
        self._output_file = output_file
        self._slicer_settings = slicer_settings
        self._material = material
        self._dualstrusion = dualstrusion
        self._task = task

    def _setprogress(self, new_progress):
        """
        posts progres update to our task, lazily
        @param new_progress progress dict of {'name':$NANME 'progress'$INT_PERCENT } 
        """
        self._task.lazy_heartbeat(new_progress)

    def _setprogress_percent(self, percent, pMin=1, pMax=99):
        """ Sets a progress update as percent, clipped to pMin, pMax
        @param percent integer percent for progress update
        @param pMin percent min, default is 1 (0 is a special 'start' case)
        @param pMax percent max, default is 99 (100 is a special 'start' case)
        """
        clamped_percent= min(pMax, max(percent, pMin))
        progress = {'name': 'slice','progress': clamped_percent }
        self._setprogress(progress)

    def _setprogress_ratio(self, current, total):
        """ sets progress based on current(int) and total(int)
        @param current: current integer index
        @param total:   expected total count
        TRICKY: This will not report 0% or 100%, those are special edge cases
        """
        ratio = int((98 * current / total) + 1)
        progress = {'name': 'slice','progress': ratio }
        self._setprogress(progress)

    def slice(self):
        raise NotImplementedError


class SubprocessSlicerException(Exception):
    pass


class SubprocessSlicer(Slicer):
    def __init__(
            self, profile, input_file, output_file, slicer_settings,
            material_name, dualstrusion, task, slicer_file):
        Slicer.__init__(
            self, profile, input_file, output_file, slicer_settings,
            material_name, dualstrusion, task)
        self._popen = None
        self._slicerlog = None
        self._code = None
        self._slicer_file = slicer_file

    def slice(self):
        try:
            progress = {'name': 'slice', 'progress': 0}
            self._setprogress(progress)
            self._prologue()
            executable = self._get_executable()
            quoted_executable = self._quote(executable)
            arguments = list(self._get_arguments())
            quoted_arguments = ' '.join(self._quote(a) for a in arguments)
            self._log.info('executable: %s', quoted_executable)
            self._log.info('command: %s', quoted_arguments)
            cwd = self._get_cwd()
            if None is cwd:
                path = executable
            else:
                path = os.path.join(cwd, executable)
            if not os.path.exists(path):
                raise conveyor.error.MissingExecutableException(path)
            self._popen = subprocess.Popen(
                arguments, executable=executable, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, cwd=cwd)
            def cancel_callback(task):
                self._popen.terminate()
            self._task.cancelevent.attach(cancel_callback)
            self._slicerlog = StringIO.StringIO()
            self._read_popen()
            slicerlog = self._slicerlog.getvalue()
            self._code = self._popen.wait()
            try:
                self._popen.stdout.close()
            except:
                self._log.debug('handled exception', exc_info=True)
            try:
                if None is not self._popen.stderr:
                    self._popen.stderr.close()
            except:
                self._log.debug('handled exception', exc_info=True)
            if (0 != self._code
                    and conveyor.task.TaskConclusion.CANCELED != self._task.conclusion):
                self._log.error(
                    '%s terminated with code %s', self._display_name,
                    self._code)
                failure = self._get_failure(None)
                self._task.fail(failure)
            else:
                self._log.debug(
                    '%s terminated with code %s', self._display_name,
                    self._code)
                self._epilogue()
                if conveyor.task.TaskConclusion.CANCELED != self._task.conclusion:
                    progress = {'name': 'slice', 'progress': 100}
                    self._setprogress(progress)
                    self._task.end(None)
        except SubprocessSlicerException as e:
            self._log.debug('handled exception', exc_info=True)
            if conveyor.task.TaskConclusion.CANCELED != self._task.conclusion:
                failure = self._get_failure(e)
                self._task.fail(failure)
        except OSError as e:
            self._log.error('operating system error', exc_info=True)
            if conveyor.task.TaskConclusion.CANCELED != self._task.conclusion:
                failure = self._get_failure(e)
                self._task.fail(failure)
        except Exception as e:
            self._log.error('unhandled exception', exc_info=True)
            if conveyor.task.TaskConclusion.CANCELED != self._task.conclusion:
                failure = self._get_failure(e)
                self._task.fail(failure)

    def _prologue(self):
        raise NotImplementedError

    def _get_executable(self):
        raise NotImplementedError

    def _get_arguments(self):
        raise NotImplementedError

    def _get_cwd(self):
        return None

    def _quote(self, s):
        quoted = ''.join(('"', unicode(s), '"'))
        return quoted

    def _read_popen(self):
        raise NotImplementedError

    def _epilogue(self):
        raise NotImplementedError

    def _get_failure(self, exception):
        slicerlog = None
        if None is not self._slicerlog:
            slicerlog = self._slicerlog.getvalue()
        failure = conveyor.util.exception_to_failure(
            exception, slicerlog=slicerlog, code=self._code)
        return failure
