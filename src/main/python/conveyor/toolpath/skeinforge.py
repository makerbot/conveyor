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
import conveyor.task

SkeinforgeSupport = conveyor.enum.enum('SkeinforgeSupport', 'NONE', 'EXTERIOR', 'FULL')

_CONVEYORDIR = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), '../../../../../')

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
    def __init__(self):
        self._log = logging.getLogger(self.__class__.__name__)

    def generate(self, stlpath, gcodepath, configuration=None):
        if None is configuration:
            configuration = SkeinforgeConfiguration()
        def runningcallback(task):
            try:
                directory = tempfile.mkdtemp()
                try:
                    tmp_stlpath = os.path.join(
                        directory, os.path.basename(stlpath))
                    shutil.copy2(stlpath, tmp_stlpath)
                    arguments = list(
                        self._getarguments(configuration, tmp_stlpath))
                    popen = subprocess.Popen(
                        arguments, executable=sys.executable,
                        stdout=subprocess.PIPE)
                    buffer = ''
                    while True:
                        data = popen.stdout.read(8192)
                        if '' == data:
                            break
                        else:
                            buffer += data
                            match = re.search('Fill layer count \d+ of \d+', buffer)
                            if None is not match:
                                print('ding: %r' % (buffer,))
                                buffer = buffer[:match.end()]
                                print('trimmed: %r' % (buffer,))
                    code = popen.wait()
                    if 0 != code:
                        raise Exception(code)
                    else:
                        tmp_gcodepath = self._gcodepath(tmp_stlpath)
                        self._postprocess(
                            gcodepath, configuration, tmp_gcodepath)
                finally:
                    shutil.rmtree(directory)
            except Exception as e:
                self._log.exception('unhandled exception')
                task.fail(e)
            else:
                task.end(None)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task

    def _gcodepath(self, path):
        root, ext = os.path.splitext(path)
        gcode = ''.join((root, '.gcode'))
        return gcode

    def _postprocess(self, gcodepath, configuration, tmp_gcodepath):
        with open(gcodepath, 'w') as fp:
            if configuration.bookend:
                path = os.path.join(
                    _CONVEYORDIR,
                    'src/main/gcode/replicator/Single_Head_start.gcode')
                self._appendgcode(fp, path)
            self._appendgcode(fp, tmp_gcodepath)
            if configuration.bookend:
                path = os.path.join(
                    _CONVEYORDIR,
                    'src/main/gcode/replicator/end.gcode')
                self._appendgcode(fp, path)

    def _appendgcode(self, wfp, path):
        with open(path, 'r') as rfp:
            for line in rfp:
                wfp.write(line)

    def _option(self, module, preference, value):
        yield '--option'
        yield ''.join((module, ':', preference, '=', unicode(value)))

    def _getarguments(self, configuration, stlpath):
        for method in (
            self._getarguments_executable,
            self._getarguments_python,
            self._getarguments_skeinforge,
            ):
                for iterable in method(configuration, stlpath):
                    for value in iterable:
                        yield value

    def _getarguments_executable(self, configuration, stlpath):
        yield (sys.executable,)

    def _getarguments_python(self, configuration, stlpath):
        yield ('-u',)
        skeinforgepath = configuration.skeinforgepath
        if None is configuration.skeinforgepath:
            skeinforgepath = os.path.join(
                _CONVEYORDIR,
                'submodule/skeinforge/skeinforge_application/skeinforge.py')
        yield (skeinforgepath,)

    def _getarguments_skeinforge(self, configuration, stlpath):
        yield ('-p',)
        profile = configuration.profile
        if None is profile:
            profile = os.path.join(
                _CONVEYORDIR,
                'src/main/skeinforge/Replicator slicing defaults')
        yield (profile,)
        for method in (
            self._getarguments_raft,
            self._getarguments_support,
            self._getarguments_bookend,
            self._getarguments_printomatic,
            self._getarguments_stl,
            ):
                for iterable in method(configuration, stlpath):
                    yield iterable

    def _getarguments_raft(self, configuration, stlpath):
        yield self._option(
            'raft.csv', 'Add Raft, Elevate Nozzle, Orbit:', configuration.raft)

    def _getarguments_support(self, configuration, stlpath):
        if SkeinforgeSupport.NONE == configuration.support:
            yield self._option('raft.csv', 'None', 'true')
            yield self._option('raft.csv', 'Empty Layers Only', 'false')
            yield self._option('raft.csv', 'Everywhere', 'false')
            yield self._option('raft.csv', 'Exterior Only', 'false')
        elif SkeinforgeSupport.EXTERIOR == configuration.support:
            yield self._option('raft.csv', 'None', 'false')
            yield self._option('raft.csv', 'Empty Layers Only', 'false')
            yield self._option('raft.csv', 'Everywhere', 'false')
            yield self._option('raft.csv', 'Exterior Only', 'true')
        elif SkeinforgeSupport.FULL == configuration.support:
            yield self._option('raft.csv', 'None', 'false')
            yield self._option('raft.csv', 'Empty Layers Only', 'false')
            yield self._option('raft.csv', 'Everywhere', 'true')
            yield self._option('raft.csv', 'Exterior Only', 'false')
        else:
            raise ValueError(configuration.support)

    def _getarguments_bookend(self, configuration, stlpath):
        if configuration.bookend:
            yield self._option('alteration.csv', 'Name of Start File:', '')
            yield self._option('alteration.csv', 'Name of End File:', '')

    def _getarguments_printomatic(self, configuration, stlpath):
        yield self._option(
            'fill.csv', 'Infill Solidity (ratio):', configuration.infillratio)
        yield self._option(
            'speed.csv', 'Feed Rate (mm/s):', configuration.feedrate)
        yield self._option(
            'speed.csv', 'Travel Feed Rate (mm/s):', configuration.travelrate)
        yield self._option(
            'speed.csv', 'Flow Rate Setting (float):', configuration.feedrate)
        yield self._option(
            'dimension.csv', 'Filament Diameter (mm):',
            configuration.filamentdiameter)
        ratio = configuration.pathwidth / configuration.layerheight
        yield self._option(
            'carve.csv', 'Perimeter Width over Thickness (ratio):', ratio)
        yield self._option(
            'fill.csv', 'Infill Width over Thickness (ratio):', ratio)
        yield self._option(
            'carve.csv', 'Layer Thickness (mm):', configuration.layerheight)
        yield self._option(
            'fill.csv', 'Extra Shells on Alternating Solid Layer (layers):',
            configuration.shells)
        yield self._option(
            'fill.csv', 'Extra Shells on Base (layers):', configuration.shells)
        yield self._option(
            'fill.csv', 'Extra Shells on Sparse Layer (layers):',
            configuration.shells)

    def _getarguments_stl(self, configuration, stlpath):
        yield (stlpath,)

def _main(argv):
    if 3 != len(argv):
        print('usage: %s STL GCODE' % (argv[0],), file=sys.stderr)
        code = 1
    else:
        logging.basicConfig()
        eventqueue = conveyor.event.geteventqueue()
        thread = threading.Thread(target=eventqueue.run)
        thread.start()
        try:
            condition = threading.Condition()
            def stoppedcallback(task):
                with condition:
                    condition.notify_all()
            generator = SkeinforgeToolpath()
            task = generator.generate(argv[1], argv[2])
            task.stoppedevent.attach(stoppedcallback)
            task.start()
            with condition:
                condition.wait()
            if conveyor.task.TaskConclusion.ENDED == task.conclusion:
                code = 0
            else:
                code = 1
        finally:
            eventqueue.quit()
            thread.join(1)
    return code

if '__main__' == __name__:
    code = _main(sys.argv)
    if None is code:
        code = 0
    sys.exit(code)
