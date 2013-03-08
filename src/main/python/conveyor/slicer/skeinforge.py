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

import csv
import os
import os.path
import re
import shutil
import sys
import tempfile
import datetime
import unittest

import conveyor.enum
import conveyor.slicer


SkeinforgeSupport = conveyor.enum.enum(
    'SkeinforgeSupport', 'NONE', 'EXTERIOR', 'FULL')


class SkeinforgeSlicer(conveyor.slicer.SubprocessSlicer):
    _name =  conveyor.slicer.Slicer.SKEINFORGE

    _display_name = 'Skeinforge'

    @staticmethod
    def get_gcode_scaffold(path):
        gcode_scaffold = conveyor.machine.GcodeScaffold()
        start_value = 'start-pla.gcode'
        end_value = 'end-pla.gcode'
        alteration_file = os.path.join(
            path, 'profiles', 'extrusion', 'ABS', 'alteration.csv')
        with open(alteration_file) as alteration_fp:
            alteration_fp.readline() # consume comment
            alteration_fp.readline() # consume header
            pos = alteration_fp.tell()
            sniffer = csv.Sniffer()
            sample = alteration_fp.read(4096)
            dialect = sniffer.sniff(sample)
            alteration_fp.seek(pos)
            reader = csv.reader(alteration_fp, dialect)
            for line in reader:
                try:
                    if 'Name of Start File:' == line[0]:
                        start_value = line[1].strip()
                    elif 'Name of End File:' == line[0]:
                        end_value = line[1].strip()
                except:
                    pass
        if '' == start_value:
            gcode_scaffold.start = []
        else:
            start_file = os.path.join(path, 'alterations', start_value)
            with open(start_file) as start_fp:
                gcode_scaffold.start = start_fp.readlines()
        if '' == end_value:
            gcode_scaffold.end = []
        else:
            end_file = os.path.join(path, 'alterations', end_value)
            with open(end_file) as end_fp:
                gcode_scaffold.end = end_fp.readlines()
        gcode_scaffold.variables = {}
        return gcode_scaffold

    def __init__(
            self, profile, input_file, output_file, slicer_settings, material,
            dualstrusion, task, slicer_file, profilepath):
        conveyor.slicer.SubprocessSlicer.__init__(
            self, profile, input_file, output_file, slicer_settings, material,
            dualstrusion, task, slicer_file)
        self._regex = re.compile(
            'Fill layer count (?P<layer>\d+) of (?P<total>\d+)\.\.\.')
        self._tmp_directory = None
        self._tmp_input_file = None
        self._profilepath = profilepath

    def _prologue(self):
        self._tmp_directory = tempfile.mkdtemp(suffix='.skeinforge')
        self._tmp_input_file = os.path.join(
            self._tmp_directory, os.path.basename(self._input_file))
        shutil.copy(self._input_file, self._tmp_input_file)

    def _get_executable(self):
        return sys.executable

    def _get_arguments(self):
        for method in (
            self._get_arguments_python,
            self._get_arguments_skeinforge,
            ):
                for iterable in method():
                    for value in iterable:
                        yield value

    def _get_arguments_python(self):
        yield ('-u',)
        yield (self._slicer_file,)

    def _get_arguments_skeinforge(self):
        if None is self._slicer_settings.path:
            yield ('-p', self._profilepath,)
            for method in (
                    self._get_arguments_raft,
                    self._get_arguments_support,
                    self._get_arguments_bookend,
                    self._get_arguments_printomatic,
                    self._get_arguments_stl,
                    ):
                for iterable in method():
                    yield iterable
        else:
            yield ('-p', self._slicer_settings.path)
            for method in (
                    self._get_arguments_bookend,
                    self._get_arguments_stl,
                    ):
                for iterable in method():
                    yield iterable

    def _get_arguments_raft(self):
        yield self._option(
            'raft.csv', 'Add Raft, Elevate Nozzle, Orbit:',
            self._slicer_settings.raft)

    def _get_arguments_support(self):
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

    _FILAMENTDIAMETER = 1.82
    _PATHWIDTH = 0.4

    def _get_arguments_bookend(self):
        yield self._option('alteration.csv', 'Name of Start File:', '')
        yield self._option('alteration.csv', 'Name of End File:', '')

    def _get_arguments_printomatic(self):
        ratio = SkeinforgeSlicer._PATHWIDTH / self._slicer_settings.layer_height
        wall_width = SkeinforgeSlicer._PATHWIDTH * self._slicer_settings.shells
        ceiling_layers = int(wall_width / self._slicer_settings.layer_height)
        yield self._option(
            'fill.csv', 'Infill Solidity (ratio):', self._slicer_settings.infill)
        yield self._option(
            'speed.csv', 'Feed Rate (mm/s):', self._slicer_settings.print_speed)
        yield self._option(
            'speed.csv', 'Travel Feed Rate (mm/s):', self._slicer_settings.travel_speed)
        yield self._option(
            'speed.csv', 'Flow Rate Setting (float):', float(self._slicer_settings.print_speed))
        yield self._option(
            'dimension.csv', 'Filament Diameter (mm):',
            SkeinforgeSlicer._FILAMENTDIAMETER)
        yield self._option(
            'carve.csv', 'Edge Width over Height (ratio):', ratio)
        yield self._option(
            'inset.csv', 'Infill Width over Thickness (ratio):', ratio)
        yield self._option(
            'carve.csv', 'Layer Height (mm):', self._slicer_settings.layer_height)
        yield self._option(
            'fill.csv', 'Solid Surface Thickness (layers):', ceiling_layers)
        yield self._option(
            'fill.csv', 'Extra Shells on Alternating Solid Layer (layers):',
            self._slicer_settings.shells-1)
        yield self._option(
            'fill.csv', 'Extra Shells on Base (layers):',
            self._slicer_settings.shells-1)
        yield self._option(
            'fill.csv', 'Extra Shells on Sparse Layer (layers):',
            self._slicer_settings.shells-1)

    def _get_arguments_stl(self):
        yield (self._tmp_input_file,)

    def _option(self, module, preference, value):
        yield '--option'
        yield ''.join((module, ':', preference, '=', unicode(value)))

    def _read_popen(self):
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
            if current_third < 3 and match is not None:
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
                if self._total_seconds(cur_datetime - sf_prev_datetime) > sf_timeout:
                    current_third = 3 # sf timeout is no longer updating, take over
                    runner = 66.0 #set this 
            elif self._total_seconds(cur_datetime - prev_datetime) > progress_time_interval:
                prev_datetime = cur_datetime 
                # fake the first 1/3 while skeinforge warms up
                if current_third == 1:
                    runner = runner + progress_increment_hack
                    self._setprogress_percent(int(runner),1,33)
                # fake the final 1/3 while skeinforge closes/writes
                elif current_third == 3:
                    runner = runner + progress_increment_hack
                    self._setprogress_percent(int(runner),66, 99)

    def _total_seconds(self, td):
        result = float(td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / float(10**6)
        return result

    def _epilogue(self):
        if conveyor.task.TaskConclusion.CANCELED != self._task.conclusion:
            with open(self._output_file, 'w') as wfp:
                root, ext = os.path.splitext(self._tmp_input_file)
                tmp_output_file = ''.join((root, '.gcode'))
                with open(tmp_output_file, 'r') as rfp:
                    for line in rfp:
                        wfp.write(line)
        shutil.rmtree(self._tmp_directory)
