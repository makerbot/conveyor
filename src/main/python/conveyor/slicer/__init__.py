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
import subprocess

import conveyor.task

class Slicer(object):
    def __init__(
        self, profile, inputpath, outputpath, with_start_end, slicer_settings,
        material, dualstrusion, task):
            self._log = logging.getLogger(self.__class__.__name__)
            self._progress = None
            self._slicerlog = None

            self._profile = profile
            self._inputpath = inputpath
            self._outputpath = outputpath
            self._with_start_end = with_start_end
            self._slicer_settings = slicer_settings
            self._material = material
            self._dualstrusion = dualstrusion
            self._task = task

    def _getname(self):
        raise NotImplementedError

    def _setprogress(self, new_progress):
		"""
		@param new_progress progress dict of {'name':$NANME 'progress'$INT_PERCENT } 
		"""
        self._task.lazy_heartbeat(new_progress, self._progress)

    def _setprogress_ratio(self, current, total):
		""" sets progress based on current(int) and total(int)
		@param current: current integer index
		@param total:	expected total count
		TRICKY: This will not report 0% or 100%, those are special edge cases
		"""
        ratio = int((98 * current / total) + 1)
        progress = {
            'name': 'slice',
            'progress': ratio
        }
        self._setprogress(progress)

    def slice(self):
        raise NotImplementedError

class SubprocessSlicerException(Exception):
    pass

class SubprocessSlicer(Slicer):
    def __init__(
        self, profile, inputpath, outputpath, with_start_end, slicer_settings,
        material, dualstrusion, task, slicerpath):
            Slicer.__init__(
                self, profile, inputpath, outputpath, with_start_end,
                slicer_settings, material, dualstrusion, task)

            self._popen = None
            self._slicerlog = None
            self._code = None

            self._slicerpath = slicerpath

    def slice(self):
        name = self._getname()
        self._log.info(
            'slicing with %s: %s -> %s', name, self._inputpath,
            self._outputpath)
        try:
            progress = {'name': 'slice', 'progress': 0}
            self._setprogress(progress)
            self._prologue()
            executable = self._getexecutable()
            quoted_executable = self._quote(executable)
            arguments = list(self._getarguments())
            quoted_arguments = ' '.join(self._quote(a) for a in arguments)
            self._log.info('command: %s %s', quoted_executable, quoted_arguments)
            self._popen = subprocess.Popen(
                arguments, executable=executable, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            def cancelcallback(task):
                self._popen.terminate()
            self._task.cancelevent.attach(cancelcallback)
            self._slicerlog = StringIO.StringIO()
            self._readpopen()
            slicerlog = self._slicerlog.getvalue()
            self._code = self._popen.wait()
            if (0 != self._code
                and conveyor.task.TaskConclusion.CANCELED != self._task.conclusion):
                    self._log.error('%s terminated with code %s', name, self._code)
                    failure = self._getfailure(None)
                    self._task.fail(failure)
            else:
                    self._log.debug('%s terminated with code %s', name, self._code)
                    self._epilogue()
                    if conveyor.task.TaskConclusion.CANCELED != self._task.conclusion:
                        progress = {'name': 'slice', 'progress': 100}
                        self._setprogress(progress)
                        self._task.end(None)
        except SubprocessSlicerException as e:
            self._log.debug('handled exception', exc_info=True)
            if conveyor.task.TaskConclusion.CANCELED != self._task.conclusion:
                failure = self._getfailure(e)
                self._task.fail(failure)
        except OSError as e:
            self._log.error('operating system error', exc_info=True)
            if conveyor.task.TaskConclusion.CANCELED != self._task.conclusion:
                failure = self._getfailure(e)
                self._task.fail(failure)
        except Exception as e:
            self._log.error('unhandled exception', exc_info=True)
            if conveyor.task.TaskConclusion.CANCELED != self._task.conclusion:
                failure = self._getfailure(e)
                self._task.fail(failure)

    def _prologue(self):
        raise NotImplementedError

    def _getexecutable(self):
        raise NotImplementedError

    def _getarguments(self):
        raise NotImplementedError

    def _quote(self, s):
        quoted = ''.join(('"', unicode(s), '"'))
        return quoted

    def _readpopen(self):
        raise NotImplementedError

    def _epilogue(self):
        raise NotImplementedError

    def _getfailure(self, exception):
        if None is not exception:
            exception = {
                'name': exception.__class__.__name__,
                'args': exception.args,
                'errno': getattr(exception, 'errno', None),
                'strerror': getattr(exception, 'strerror', None),
                'filename': getattr(exception, 'filename', None),
                'winerror': getattr(exception, 'winerror', None)
            }
        slicerlog = None
        if None is not self._slicerlog:
            slicerlog = self._slicerlog.getvalue()
        failure = {
            'exception': exception,
            'slicerlog': slicerlog,
            'code': self._code
        }
        return failure
