# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/toolpath/miraclegrue.py
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

import logging
import os
import subprocess
import sys
import threading
import tempfile
import traceback
import json

import conveyor.event
import conveyor.printer.s3g # TODO: aww, bad coupling

class MiracleGrueConfiguration(object):
    def __init__(self):
        self.miraclegruepath = None
        self.miracleconfigpath = None

class MiracleGrueToolpath(object):
    def __init__(self, configuration):
        self._configuration = configuration
        self._log = logging.getLogger(self.__class__.__name__)

    def _parse_progress(self, line):
        progress = None
        try:
            dct = json.loads(line)
        except ValueError:
            pass
        else:
            if (isinstance(dct, dict) and 'progress' == dct.get('type')
                and 'totalPercentComplete' in dct):
                    progress = {
                        'name': 'slice',
                        'progress': int(dct['totalPercentComplete'])
                    }
        return progress

    def _update_progress(self, current_progress, new_progress, task):
        if None is not new_progress and new_progress != current_progress:
            current_progress = new_progress
            task.heartbeat(current_progress)
        return current_progress

    def slice(
        self, profile, inputpath, outputpath, with_start_end,
        slicer_settings, material, task):
            self._log.info('slicing with Miracle Grue')
            try:
                current_progress = None
                new_progress = {
                    'name': 'slice',
                    'progress': 0
                }
                current_progress = self._update_progress(
                    current_progress, new_progress, task)
                driver = conveyor.printer.s3g.S3gDriver()
                if not with_start_end:
                    startpath = None
                    endpath = None
                else:
                    startgcode, endgcode, variables = driver._get_start_end_variables(
                        profile, slicer_settings, material)
                    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as startfp:
                        startpath = startfp.name
                        for line in startgcode:
                            print(line, file=startfp)
                    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as endfp:
                        endpath = endfp.name
                        for line in endgcode:
                            print(line, file=endfp)
                with tempfile.NamedTemporaryFile(suffix='.config', delete=False) as configfp:
                    configpath = configfp.name
                    self._generateconfig(slicer_settings, material, configfp)
                arguments = list(
                    self._getarguments(
                        configpath, inputpath, outputpath, startpath,
                        endpath))
                self._log.debug('arguments=%r', arguments)
                popen = subprocess.Popen(
                    arguments, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
                self._log.debug('popen=%r, popen.pid=%r, popen.returncode=%r', popen, popen.pid, popen.returncode) # TODO: remove this silly temporary debugging output
                def cancelcallback(task):
                    popen.terminate()
                task.cancelevent.attach(cancelcallback)
                self._log.debug('reading from miracle grue')
                while True:
                    line = popen.stdout.readline()
                    if '' == line:
                        break
                    else:
                        self._log.debug('miracle-grue: %s', line)
                        new_progress = self._parse_progress(line)
                        current_progress = self._update_progress(
                            current_progress, new_progress, task)
                code = popen.wait()
                self._log.debug('miracle-grue terminated with code %s', code)
                if None is not startpath:
                    os.unlink(startpath)
                if None is not endpath:
                    os.unlink(endpath)
                if 0 != code:
                    raise Exception(code)
            except Exception as e:
                self._log.exception('unhandled exception')
                task.fail(e)
                raise
            else:
                new_progress = {
                    'name': 'slice',
                    'progress': 100
                }
                current_progress = self._update_progress(
                    current_progress, new_progress, task)
                task.end(None)

    def _generateconfig(self, slicer_settings, material, fp):
        raftLayers = 2
        fanLayer = 2
        if slicer_settings.raft:
            fanLayer += raftLayers
        dct = {
            'infillDensity'           : slicer_settings.infill,
            'numberOfShells'          : slicer_settings.shells,
            'insetDistanceMultiplier' : 0.9,
            'roofLayerCount'          : 4,
            'floorLayerCount'         : 4,
            'layerWidthRatio'         : 1.45,
            'coarseness'              : 0.05,
            'doGraphOptimization'     : True,
            'rapidMoveFeedRateXY'     : slicer_settings.travel_speed,
            'rapidMoveFeedRateZ'      : 23.0,
            'doRaft'                  : slicer_settings.raft,
            'raftLayers'              : raftLayers,
            'raftBaseThickness'       : 0.6,
            'raftInterfaceThickness'  : 0.3,
            'raftOutset'              : 6.0,
            'raftModelSpacing'        : 0.0,
            'raftDensity'             : 0.2,
            'doSupport'               : slicer_settings.support,
            'supportMargin'           : 1.5,
            'supportDensity'          : 0.2,
            'doFanCommand'            : 'PLA' == material,
            'fanLayer'                : fanLayer,
            'bedZOffset'              : 0.0,
            'layerHeight'             : slicer_settings.layer_height,
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
                    'feedrate': slicer_settings.print_speed
                },
                'infill': {
                    'feedrate': slicer_settings.print_speed
                },
                'firstlayer': {
                    'feedrate': 40.0
                },
                'outlines': {
                    'feedrate': 40.0
                }
            }
        }
        json.dump(dct, fp, indent=8)
        s = json.dumps(dct)
        self._log.debug('miracle grue configuration: %s', s)

    def _getarguments(
        self, configpath, inputpath, outputpath, startpath, endpath):
            for method in (
                self._getarguments_executable,
                self._getarguments_miraclegrue,
                ):
                    for iterable in method(
                        configpath, inputpath, outputpath, startpath,
                        endpath):
                            for value in iterable:
                                yield value

    def _getarguments_executable(
        self, configpath, inputpath, outputpath, startpath, endpath):
            yield (self._configuration.miraclegruepath,)

    def _getarguments_miraclegrue(
        self, configpath, inputpath, outputpath, startpath, endpath):
            yield ('-c', configpath,)
            yield ('-o', outputpath,)
            if None is not startpath:
                yield ('-s', startpath,)
            if None is not endpath:
                yield ('-e', endpath,)
            yield ('-j',)
            yield (inputpath,)
