# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/slicer/miraclegrue.py
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

import json
import os
import tempfile

import conveyor.event
import conveyor.json
import conveyor.machine
import conveyor.slicer
import conveyor.util

class MiracleGrueSlicer(conveyor.slicer.SubprocessSlicer):
    _name = conveyor.slicer.Slicer.MIRACLEGRUE

    _display_name = 'Miracle Grue'

    @staticmethod
    def get_gcode_scaffold(path):
        gcode_scaffold = conveyor.machine.GcodeScaffold()
        dirname = os.path.dirname(path)
        with open(path) as config_fp:
            config = conveyor.json.load(config_fp)
        start_value = config.get('startGcode', 'start.gcode')
        if None is start_value:
            gcode_scaffold.start = []
        else:
            start_file = os.path.join(dirname, start_value)
            with open(start_file) as start_fp:
                gcode_scaffold.start = start_fp.readlines()
        end_value = config.get('endGcode', 'end.gcode')
        if None is end_value:
            gcode_scaffold.end = []
        else:
            end_file = os.path.join(dirname, end_value)
            with open(end_file) as end_fp:
                gcode_scaffold.end = end_fp.readlines()
        gcode_scaffold.variables = {}
        return gcode_scaffold

    def __init__(
            self, profile, input_file, output_file, slicer_settings, material,
            dualstrusion, task, slicer_file, config_file):
        conveyor.slicer.SubprocessSlicer.__init__(
            self, profile, input_file, output_file, slicer_settings, material,
            dualstrusion, task, slicer_file)
        self._config_file = config_file
        self._tmp_config_file = None

    def _prologue(self):
        if None is not self._slicer_settings.path:
            config = self._get_config_custom()
        else:
            config = self._get_config_printomatic()
        s = json.dumps(config)
        self._log.debug('using miracle grue configuration: %s', s)
        with tempfile.NamedTemporaryFile(suffix='.config', delete=False) as tmp_config_fp:
            self._tmp_config_file = tmp_config_fp.name
            json.dump(config, tmp_config_fp, indent=8)

    def _get_config_custom(self):
        with open(self._slicer_settings.path) as config_fp:
            config = conveyor.json.load(config_fp)
        config['defaultExtruder'] = int(self._slicer_settings.extruder)
        config['startGcode'] = None
        config['endGcode'] = None
        return config

    def _get_config_printomatic(self):
        config_file = self._get_config_printomatic_file()
        with open(config_file) as fp:
            config = conveyor.json.load(fp)
        config['infillDensity'] = self._slicer_settings.infill
        config['numberOfShells'] = self._slicer_settings.shells
        config['rapidMoveFeedRateXY'] = self._slicer_settings.travel_speed
        config['doRaft'] = self._slicer_settings.raft
        config['doSupport'] = self._slicer_settings.support
        config['doFanCommand'] = 'PLA' == self._material
        config['layerHeight'] = self._slicer_settings.layer_height
        config['defaultExtruder'] = int(self._slicer_settings.extruder)
        config['extrusionProfiles']['insets']['feedrate'] = self._slicer_settings.print_speed
        config['extrusionProfiles']['infill']['feedrate'] = self._slicer_settings.print_speed
        if self._slicer_settings.raft:
            # Turn on the fan immediately after the raft.
            raftLayers = config['raftLayers']
            config['fanLayer'] = raftLayers
        if self._dualstrusion:
            config['doPutModelOnPlatform'] = False
        config['startGcode'] = None
        config['endGcode'] = None
        return config

    def _get_config_printomatic_file(self):
        if 'ABS' == self._material:
            config_abs = os.path.join(self._config_file, 'miracle-abs.config')
            if os.path.exists(config_abs):
                return config_abs
        elif 'PLA' == self._material:
            config_pla = os.path.join(self._config_file, 'miracle-pla.config')
            if os.path.exists(config_pla):
                return config_pla
        else:
            raise ValueError()
        config_generic = os.path.join(self._config_file, 'miracle.config')
        return config_generic

    def _get_executable(self):
        executable = os.path.abspath(self._slicer_file)
        return executable

    def _get_arguments(self):
        for iterable in self._get_arguments_miraclegrue():
            for value in iterable:
                yield value

    def _get_arguments_miraclegrue(self):
        yield (self._get_executable(),)
        yield ('-c', self._tmp_config_file,)
        yield ('-o', self._output_file,)
        yield ('-j',)
        yield (self._input_file,)

    def _get_cwd(self):
        if None is self._slicer_settings.path:
            cwd = None
        else:
            cwd = os.path.dirname(self._slicer_settings.path)
        return cwd

    def _read_popen(self):
        while True:
            line = self._popen.stdout.readline()
            if '' == line:
                break
            else:
                self._slicerlog.write(line)
                try:
                    dct = json.loads(line)
                except ValueError:
                    pass
                else:
                    if (isinstance(dct, dict) and 'progress' == dct.get('type')
                        and 'totalPercentComplete' in dct):
                            percent = int(dct['totalPercentComplete'])
                            self._setprogress_ratio(percent, 100)

    def _epilogue(self):
        pass
