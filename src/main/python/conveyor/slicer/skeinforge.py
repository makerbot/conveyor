# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/slicer/skeinforge.py
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

import os
import os.path
import re
import shutil
import sys
import tempfile
import datetime
import unittest

import conveyor.enum
import conveyor.machine.s3g # TODO: aww, more bad coupling
import conveyor.slicer

SkeinforgeSupport = conveyor.enum.enum('SkeinforgeSupport', 'NONE', 'EXTERIOR', 'FULL')

class SkeinforgeSlicer(conveyor.slicer.SubprocessSlicer):
    def __init__(
        self, profile, inputpath, outputpath, with_start_end, slicer_settings,
        material, task, slicerpath, profilepath):
            conveyor.slicer.SubprocessSlicer.__init__(
                self, profile, inputpath, outputpath, with_start_end,
                slicer_settings, material, task, slicerpath)

            self._regex = re.compile(
                'Fill layer count (?P<layer>\d+) of (?P<total>\d+)\.\.\.')
            self._tmp_directory = None
            self._tmp_inputpath = None

            self._profilepath = profilepath

    def _getname(self):
        return 'Skeinforge'

    def _prologue(self):
        self._tmp_directory = tempfile.mkdtemp()
        self._tmp_inputpath = os.path.join(
            self._tmp_directory, os.path.basename(self._inputpath))
        shutil.copy2(self._inputpath, self._tmp_inputpath)

    def _getexecutable(self):
        return sys.executable

    def _getarguments(self):
        for method in (
            self._getarguments_python,
            self._getarguments_skeinforge,
            ):
                for iterable in method():
                    for value in iterable:
                        yield value

    def _getarguments_python(self):
        yield ('-u',)
        yield (self._slicerpath,)

    def _getarguments_skeinforge(self):
        if self._slicer_settings.path is None:
            yield ('-p', self._profilepath,)
            for method in (
                self._getarguments_raft,
                self._getarguments_support,
                self._getarguments_bookend,
                self._getarguments_printomatic,
                self._getarguments_stl,
                ):
                    for iterable in method():
                        yield iterable
        else:
            yield ('-p', self._slicer_settings.path)
            for iterable in self._getarguments_stl():
                yield iterable

    def _getarguments_raft(self):
        yield self._option(
            'raft.csv', 'Add Raft, Elevate Nozzle, Orbit:',
            self._slicer_settings.raft)

    def _getarguments_support(self):
        # TODO: Support the exterior support. Endless domain model problems... :(
        if not self._slicer_settings.support:
            support = SkeinforgeSupport.NONE
        else:
            support = SkeinforgeSupport.FULL
        if SkeinforgeSupport.NONE == support:
            yield self._option('raft.csv', 'None', 'true')
            yield self._option('raft.csv', 'Empty Layers Only', 'false')
            yield self._option('raft.csv', 'Everywhere', 'false')
            yield self._option('raft.csv', 'Exterior Only', 'false')
        elif SkeinforgeSupport.EXTERIOR == support:
            yield self._option('raft.csv', 'None', 'false')
            yield self._option('raft.csv', 'Empty Layers Only', 'false')
            yield self._option('raft.csv', 'Everywhere', 'false')
            yield self._option('raft.csv', 'Exterior Only', 'true')
        elif SkeinforgeSupport.FULL == support:
            yield self._option('raft.csv', 'None', 'false')
            yield self._option('raft.csv', 'Empty Layers Only', 'false')
            yield self._option('raft.csv', 'Everywhere', 'true')
            yield self._option('raft.csv', 'Exterior Only', 'false')
        else:
            raise ValueError(self._slicer_settings.support)

    # TODO: find a home for these values.

    _BOOKEND = True
    _FILAMENTDIAMETER = 1.82
    _PATHWIDTH = 0.4

    def _getarguments_bookend(self):
        if SkeinforgeSlicer._BOOKEND:
            yield self._option('alteration.csv', 'Name of Start File:', '')
            yield self._option('alteration.csv', 'Name of End File:', '')

    def _getarguments_printomatic(self):
        yield self._option(
            'fill.csv', 'Infill Solidity (ratio):', self._slicer_settings.infill)
        yield self._option(
            'speed.csv', 'Feed Rate (mm/s):', self._slicer_settings.print_speed)
        yield self._option(
            'speed.csv', 'Travel Feed Rate (mm/s):', self._slicer_settings.travel_speed)
        yield self._option(
            'speed.csv', 'Flow Rate Setting (float):', self._slicer_settings.print_speed)
        yield self._option(
            'dimension.csv', 'Filament Diameter (mm):',
            SkeinforgeSlicer._FILAMENTDIAMETER)
        ratio = SkeinforgeSlicer._PATHWIDTH / self._slicer_settings.layer_height
        yield self._option(
            'carve.csv', 'Perimeter Width over Thickness (ratio):', ratio)
        yield self._option(
            'fill.csv', 'Infill Width over Thickness (ratio):', ratio)
        yield self._option(
            'carve.csv', 'Layer Height (mm):', self._slicer_settings.layer_height)
        yield self._option(
            'fill.csv', 'Extra Shells on Alternating Solid Layer (layers):',
            self._slicer_settings.shells-1)
        yield self._option(
            'fill.csv', 'Extra Shells on Base (layers):',
            self._slicer_settings.shells-1)
        yield self._option(
            'fill.csv', 'Extra Shells on Sparse Layer (layers):',
            self._slicer_settings.shells-1)

    def _getarguments_stl(self):
        yield (self._tmp_inputpath,)

    def _option(self, module, preference, value):
        yield '--option'
        yield ''.join((module, ':', preference, '=', unicode(value)))

    def _readpopen(self):
        """
        Read the output of Skeinforge and turn them into progress updates.
        SF does a poor job emitting progress updates, so we need to inject
        artificial updates for it.  We have 3 stages of updates, and asymptotically 
        increase them.  The first set goes up to 33, the second (natural) set goes from
        33 to 66, and the final (artifical) set goes from 66 to 99.
        """
        buffer = ''
        #first_third_done = False
        #second_third_done = False
        sf_timeout= 15 #sf timeout in seconds
		runner = 0.0
		current_third = 1 # 1'st 3rd, fake, 2nd-third read, 3rd-3rd fake
		faker_min, faker_max = 1, 33
        progress_increment_hack = .5
        progress_time_interval = 1
        cur_datetime = datetime.datetime.now()
        prev_datetime = cur_datetime 
        sf_prev_datetime = cur_datetime 
        while True:
            cur_datetime = datetime.datetime.now()
            data = self._popen.stdout.read(1) # :.(
			# no good data, leave this loop forevar
            if '' == data:
                break
			self._slicerlog.write(data)
			buffer += data
			match = self._regex.search(buffer)
			if current_third == 1 and match is not None:
				sf_prev_datetime = datetime.datetime.now()
				current_third = 2
				buffer = buffer[match.end():]
				layer = int(match.group('layer'))
				total = int(match.group('total'))
				progress = 100*layer/total
				self._setprogress_percent(progress,33, 66)
			# SF doesnt always emit updates for all its layers, we
			# take a timestamp diff to see if we should begin 
			# artificial update for the last 33% 
			elif current_third == 2:
				if(cur_datetime - sf_prev_datetime).total_seconds() > sf_timeout:
					current_third = 3 # sf timeout is no longer updating, take over
					runner = 33.0 #set this 
			elif (cur_datetime - prev_datetime).total_seconds() > progress_time_interval:
				prev_datetime = cur_datetime 
				# fake the first 1/3 while skeinforge warms up
				if current_third == 1:
					runner = runner + progress_increment_hack
					self._setprogress_percent(int(runner),1,33)
				# fake the final 1/3 while skeinforge closes/writes
				elif current_third == 3:
					runner = runner + progress_increment_hack
					self._setprogress_percent(int(runner),66, 99)


    def _epilogue(self):
        if conveyor.task.TaskConclusion.CANCELED != self._task.conclusion:
            driver = conveyor.machine.s3g.S3gDriver()
            startgcode, endgcode, variables = driver._get_start_end_variables(
                self._profile, self._slicer_settings, self._material)
            with open(self._outputpath, 'w') as wfp:
                if self._with_start_end:
                    for line in startgcode:
                        print(line, file=wfp)
                root, ext = os.path.splitext(self._tmp_inputpath)
                tmp_outputpath = ''.join((root, '.gcode'))
                with open(tmp_outputpath, 'r') as rfp:
                    for line in rfp:
                        wfp.write(line)
                if self._with_start_end:
                    for line in endgcode:
                        print(line, file=wfp)
        shutil.rmtree(self._tmp_directory)
