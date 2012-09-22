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
import conveyor.printer.s3g # TODO: aww, bad coupling
import conveyor.slicer

class MiracleGrueSlicer(conveyor.slicer.SubprocessSlicer):
    def __init__(
        self, profile, inputpath, outputpath, with_start_end, slicer_settings,
        material, task, slicerpath):
            conveyor.slicer.SubprocessSlicer.__init__(
                self, profile, inputpath, outputpath, with_start_end,
                slicer_settings, material, task, slicerpath)

            self._startpath = None
            self._endpath = None
            self._configpath = None

    def _getname(self):
        return 'Miracle Grue'

    def _prologue(self):
        if self._with_start_end:
            startgcode, endgcode, variables = driver._get_start_end_variables(
                profile, slicer_settings, material)
            with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as startfp:
                self._startpath = startfp.name
                for line in startgcode:
                    print(line, file=startfp)
            with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as endfp:
                self._endpath = endfp.name
                for line in endgcode:
                    print(line, file=endfp)
        config = self._getconfig()
        s = json.dumps(config)
        self._log.debug('miracle grue configuration: %s', s)
        with tempfile.NamedTemporaryFile(suffix='.config', delete=False) as configfp:
            self._configpath = configfp.name
            json.dump(config, configfp, indent=8)

    def _getconfig(self):
        # TODO: yes, yes, load a file and override its values..
        config = {
            'infillDensity'           : self._slicer_settings.infill,
            'numberOfShells'          : self._slicer_settings.shells,
            'insetDistanceMultiplier' : 0.9,
            'roofLayerCount'          : 4,
            'floorLayerCount'         : 4,
            'layerWidthRatio'         : 1.45,
            'coarseness'              : 0.05,
            'doGraphOptimization'     : True,
            'rapidMoveFeedRateXY'     : self._slicer_settings.travel_speed,
            'rapidMoveFeedRateZ'      : 23.0,
            'doRaft'                  : self._slicer_settings.raft,
            'raftLayers'              : 2,
            'raftBaseThickness'       : 0.6,
            'raftInterfaceThickness'  : 0.3,
            'raftOutset'              : 6.0,
            'raftModelSpacing'        : 0.0,
            'raftDensity'             : 0.2,
            'doSupport'               : self._slicer_settings.support,
            'supportMargin'           : 1.5,
            'supportDensity'          : 0.2,
            'doFanCommand'            : 'PLA' == self._material,
            'fanLayer'                : 2,
            'bedZOffset'              : 0.0,
            'layerHeight'             : self._slicer_settings.layer_height,
            'startX'                  : -110.4,
            'startY'                  : -74.0,
            'startZ'                  : 0.2,
            'doPrintProgress'         : True,
            'defaultExtruder'         : 0, # TODO: there's a field in SlicerConfiguration for this, but... so many other things need to be changed for it to work
            'extruderProfiles'        : [
                {
                    'firstLayerExtrusionProfile' : 'firstlayer',
                    'insetsExtrusionProfile'     : 'insets',
                    'infillsExtrusionProfile'    : 'infill',
                    'outlinesExtrusionProfile'   : 'outlines',
                    'feedDiameter'               : 1.82,
                    'nozzleDiameter'             : 0.4,
                    'retractDistance'            : 1.0,
                    'retractRate'                : 20.0,
                    'restartExtraDistance'       : 0.0
                },
                {
                    'firstLayerExtrusionProfile' : 'firstlayer',
                    'insetsExtrusionProfile'     : 'insets',
                    'infillsExtrusionProfile'    : 'infill',
                    'outlinesExtrusionProfile'   : 'outlines',
                    'feedDiameter'               : 1.82,
                    'nozzleDiameter'             : 0.4,
                    'retractDistance'            : 1.0,
                    'retractRate'                : 20.0,
                    'restartExtraDistance'       : 0.0
                }
            ],
            'extrusionProfiles': {
                'insets': {
                    'feedrate': self._slicer_settings.print_speed
                },
                'infill': {
                    'feedrate': self._slicer_settings.print_speed
                },
                'firstlayer': {
                    'feedrate': 40.0
                },
                'outlines': {
                    'feedrate': 40.0
                }
            }
        }
        return config

    def _getexecutable(self):
        return self._slicerpath

    def _getarguments(self):
        for iterable in self._getarguments_miraclegrue():
            for value in iterable:
                yield value

    def _getarguments_miraclegrue(self):
        yield (self._getexecutable(),)
        yield ('-c', self._configpath,)
        yield ('-o', self._outputpath,)
        if None is not self._startpath:
            yield ('-s', self._startpath,)
        if None is not self._endpath:
            yield ('-e', self._endpath,)
        yield ('-j',)
        yield (self._inputpath,)

    def _readpopen(self):
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
        if None is not self._startpath:
            os.unlink(self._startpath)
        if None is not self._endpath:
            os.unlink(self._endpath)
        if None is not self._configpath:
            os.unlink(self._configpath)
