# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/toolpath/skeinforge.py
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
import os
import os.path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import traceback

import conveyor.enum
import conveyor.event
import conveyor.printer.s3g # TODO: aww, more bad coupling

SkeinforgeSupport = conveyor.enum.enum('SkeinforgeSupport', 'NONE', 'EXTERIOR', 'FULL')

class SkeinforgeConfiguration(object):
    def __init__(self):
        self.skeinforgepath = None
        self.profile = None
        self.raft = False
        self.support = SkeinforgeSupport.NONE
        self.bookend = True
        self.infillratio = 0.1
        self.feedrate = 40.0
        self.travelrate = 55.0
        self.filamentdiameter = 1.82
        self.pathwidth = 0.4
        self.layerheight = 0.27
        self.shells = 1

class SkeinforgeToolpath(object):
    def __init__(self, configuration):
        self._configuration = configuration
        self._log = logging.getLogger(self.__class__.__name__)
        self._regex = re.compile(
            'Fill layer count (?P<layer>\d+) of (?P<total>\d+)\.\.\.')

    def _update_progress(self, current_progress, new_progress, task):
        if None is not new_progress and new_progress != current_progress:
            current_progress = new_progress
            task.heartbeat(current_progress)
        return current_progress

    def slice(
        self, profile, inputpath, outputpath, with_start_end,
        slicer_settings, material, task):
            self._log.info('slicing with Skeinforge')
            try:
                current_progress = None
                new_progress = {
                    'name': 'slice',
                    'progress': 0
                }
                current_progress = self._update_progress(
                    current_progress, new_progress, task)
                directory = tempfile.mkdtemp()
                try:
                    tmp_inputpath = os.path.join(
                        directory, os.path.basename(inputpath))
                    shutil.copy2(inputpath, tmp_inputpath)
                    arguments = list(
                        self._getarguments(tmp_inputpath))
                    self._log.debug('arguments=%r', arguments)

                    quoted_arguments = [''.join(('"', str(a), '"')) for a in arguments]
                    self._log.info('quoted_arguments=%s', ' '.join(quoted_arguments))

                    popen = subprocess.Popen(
                        arguments, executable=sys.executable,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    log = StringIO.StringIO()
                    buffer = ''
                    while True:
                        data = popen.stdout.read(1) # :(
                        if '' == data:
                            break
                        else:
                            log.write(data)
                            buffer += data
                            match = self._regex.search(buffer)
                            if None is not match:
                                buffer = buffer[match.end():]
                                layer = int(match.group('layer'))
                                total = int(match.group('total'))
                                progress = {
                                    "layer" : layer,
                                    "total" : total,
                                    "name" : "slice",
                                    "progress" : int((layer/float(total))*100),
                                }
                                task.heartbeat(progress)
                    code = popen.wait()
                    self._log.debug(
                        'Skeinforge terminated with status code %d', code)
                    if 0 != code:
                        self._log.error('%s', log.getvalue())
                        raise Exception(code)
                    else:
                        self._log.debug('%s', log.getvalue())
                        tmp_outputpath = self._outputpath(tmp_inputpath)
                        self._postprocess(
                            profile, slicer_settings, material, outputpath,
                            tmp_outputpath, with_start_end)
                finally:
                    shutil.rmtree(directory)
            except Exception as e:
                self._log.exception('unhandled exception')
                task.fail(e)
            else:
                task.end(None)

    def _outputpath(self, path):
        root, ext = os.path.splitext(path)
        gcode = ''.join((root, '.gcode'))
        return gcode

    def _postprocess(
        self, profile, slicer_settings, material, outputpath, tmp_outputpath,
        with_start_end):
            driver = conveyor.printer.s3g.S3gDriver()
            startgcode, endgcode, variables = driver._get_start_end_variables(
                profile, slicer_settings, material)
            with open(outputpath, 'w') as fp:
                if with_start_end:
                    for line in startgcode:
                        print(line, file=fp)
                self._appendgcode(fp, tmp_outputpath)
                if with_start_end:
                    for line in endgcode:
                        print(line, file=fp)

    def _appendgcode(self, wfp, path):
        with open(path, 'r') as rfp:
            for line in rfp:
                wfp.write(line)

    def _option(self, module, preference, value):
        yield '--option'
        yield ''.join((module, ':', preference, '=', unicode(value)))

    def _getarguments(self, inputpath):
        for method in (
            self._getarguments_executable,
            self._getarguments_python,
            self._getarguments_skeinforge,
            ):
                for iterable in method(inputpath):
                    for value in iterable:
                        yield value

    def _getarguments_executable(self, inputpath):
        yield (sys.executable,)

    def _getarguments_python(self, inputpath):
        yield ('-u',)
        yield (self._configuration.skeinforgepath,)

    def _getarguments_skeinforge(self, inputpath):
        yield ('-p', self._configuration.profile,)
        for method in (
            self._getarguments_raft,
            self._getarguments_support,
            self._getarguments_bookend,
            self._getarguments_printomatic,
            self._getarguments_stl,
            ):
                for iterable in method(inputpath):
                    yield iterable

    def _getarguments_raft(self, inputpath):
        yield self._option(
            'raft.csv', 'Add Raft, Elevate Nozzle, Orbit:', self._configuration.raft)

    def _getarguments_support(self, inputpath):
        # TODO: Support the exterior support. Endless domain model problems... :(
        if not self._configuration.support:
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
            raise ValueError(self._configuration.support)

    def _getarguments_bookend(self, inputpath):
        if self._configuration.bookend:
            yield self._option('alteration.csv', 'Name of Start File:', '')
            yield self._option('alteration.csv', 'Name of End File:', '')

    def _getarguments_printomatic(self, inputpath):
        yield self._option(
            'fill.csv', 'Infill Solidity (ratio):', self._configuration.infillratio)
        yield self._option(
            'speed.csv', 'Feed Rate (mm/s):', self._configuration.feedrate)
        yield self._option(
            'speed.csv', 'Travel Feed Rate (mm/s):', self._configuration.travelrate)
        yield self._option(
            'speed.csv', 'Flow Rate Setting (float):', self._configuration.feedrate)
        yield self._option(
            'dimension.csv', 'Filament Diameter (mm):',
            self._configuration.filamentdiameter)
        ratio = self._configuration.pathwidth / self._configuration.layerheight
        yield self._option(
            'carve.csv', 'Perimeter Width over Thickness (ratio):', ratio)
        yield self._option(
            'fill.csv', 'Infill Width over Thickness (ratio):', ratio)
        yield self._option(
            'carve.csv', 'Layer Height (mm):', self._configuration.layerheight)
        yield self._option(
            'fill.csv', 'Extra Shells on Alternating Solid Layer (layers):',
            self._configuration.shells-1)
        yield self._option(
            'fill.csv', 'Extra Shells on Base (layers):',
            self._configuration.shells-1)
        yield self._option(
            'fill.csv', 'Extra Shells on Sparse Layer (layers):',
            self._configuration.shells-1)

    def _getarguments_stl(self, inputpath):
        yield (inputpath,)
