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

from decimal import *

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

SkeinforgeSupport = conveyor.enum.enum('SkeinforgeSupport', 'NONE', 'EXTERIOR', 'FULL')

class SkeinforgeConfiguration(object):
    def __init__(self):
        self.skeinforgepath = None
        self.profile = None
        self.raft = False
        self.support = SkeinforgeSupport.NONE
        self.bookend = True
        self.infillratio = Decimal('0.1')
        self.feedrate = Decimal('40')
        self.travelrate = Decimal('55')
        self.filamentdiameter = Decimal('1.82')
        self.pathwidth = Decimal('0.4')
        self.layerheight = Decimal('0.27')
        self.shells = 1

class SkeinforgeToolpath(object):
    def __init__(self, configuration):
        self._configuration = configuration
        self._log = logging.getLogger(self.__class__.__name__)
        self._regex = re.compile(
            'Fill layer count (?P<layer>\d+) of (?P<total>\d+)\.\.\.')

    def slice(self, profile, inputpath, outputpath, with_start_end, task):
        self._log.info('slicing with Skeinforge')
        try:
            directory = tempfile.mkdtemp()
            try:
                tmp_inputpath = os.path.join(
                    directory, os.path.basename(inputpath))
                shutil.copy2(inputpath, tmp_inputpath)
                arguments = list(
                    self._getarguments(tmp_inputpath))
                self._log.debug('arguments=%r', arguments)
                popen = subprocess.Popen(
                    arguments, executable=sys.executable,
                    stdout=subprocess.PIPE)
                log = ''
                buffer = ''
                while True:
                    data = popen.stdout.read(1) # :(
                    if '' == data:
                        break
                    else:
                        buffer += data
                        match = self._regex.search(buffer)
                        if None is not match:
                            buffer = buffer[match.end():]
                            layer = int(match.group('layer'))
                            total = int(match.group('total'))
                            progress = {
                                "layer" : layer,
                                "total" : total,
                                "progress" : layer/float(total),
                                }
                            task.heartbeat(progress)
                code = popen.wait()
                self._log.debug(
                    'Skeinforge terminated with status code %d', code)
                if 0 != code:
                    raise Exception(code)
                else:
                    tmp_outputpath = self._outputpath(tmp_inputpath)
                    self._postprocess(
                        profile, outputpath, tmp_outputpath,
                        with_start_end)
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

    def _postprocess(self, profile, outputpath, tmp_outputpath, with_start_end):
        with open(outputpath, 'w') as fp:
            if with_start_end:
                for line in profile.values['print_start_sequence']:
                    print(line, file=fp)
            self._appendgcode(fp, tmp_outputpath)
            if with_start_end:
                for line in profile.values['print_end_sequence']:
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
        if SkeinforgeSupport.NONE == self._configuration.support:
            yield self._option('raft.csv', 'None', 'true')
            yield self._option('raft.csv', 'Empty Layers Only', 'false')
            yield self._option('raft.csv', 'Everywhere', 'false')
            yield self._option('raft.csv', 'Exterior Only', 'false')
        elif SkeinforgeSupport.EXTERIOR == self._configuration.support:
            yield self._option('raft.csv', 'None', 'false')
            yield self._option('raft.csv', 'Empty Layers Only', 'false')
            yield self._option('raft.csv', 'Everywhere', 'false')
            yield self._option('raft.csv', 'Exterior Only', 'true')
        elif SkeinforgeSupport.FULL == self._configuration.support:
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
            'carve.csv', 'Layer Thickness (mm):', self._configuration.layerheight)
        yield self._option(
            'fill.csv', 'Extra Shells on Alternating Solid Layer (layers):',
            self._configuration.shells)
        yield self._option(
            'fill.csv', 'Extra Shells on Base (layers):', self._configuration.shells)
        yield self._option(
            'fill.csv', 'Extra Shells on Sparse Layer (layers):',
            self._configuration.shells)

    def _getarguments_stl(self, inputpath):
        yield (inputpath,)
