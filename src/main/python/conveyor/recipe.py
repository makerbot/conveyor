# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4
# conveyor/src/main/python/conveyor/recipe.py
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

import contextlib
import logging
import makerbot_driver
import os
import os.path
import subprocess
import tempfile

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.domain
import conveyor.dualstrusion
import conveyor.enum
import conveyor.process
import conveyor.task


class RecipeManager(object):
    def __init__(self, server, config):
        self._config = config
        self._server = server
        self._log = logging.getLogger(self.__class__.__name__)

    def getrecipe(self, job):
        root, ext = os.path.splitext(job.path)
        if '.gcode' == ext.lower():
            recipe = self._getrecipe_gcode(job)
        elif '.stl' == ext.lower():
            recipe = self._getrecipe_stl(job)
        elif '.thing' == ext.lower():
            recipe = self._getrecipe_thing(job)
        else:
            raise UnsupportedModelTypeException(job.path)
        return recipe

    def _getrecipe_gcode(self, job):
        if not os.path.exists(job.path):
            raise MissingFileException(job.path)
        elif not os.path.isfile(job.path):
            raise NotFileException(job.path)
        else:
            recipe = _GcodeRecipe(self._server, self._config, job, job.path)
        return recipe

    def _getrecipe_stl(self, job):
        if not os.path.exists(job.path):
            raise MissingPathExceptoin(job.path)
        elif not os.path.isfile(job.path):
            raise NotFileException(job.path)
        else:
            recipe = _StlRecipe(self._server, self._config, job, job.path)
            return recipe

    def _getrecipe_thing(self, job):
        if not os.path.exists(job.path):
            raise MissingFileException(job.path)
        else:
            thing_dir = tempfile.mkdtemp(suffix='.thing')
            popen = subprocess.Popen(
                ['../Prototype/obj/unified_mesh_hack', job.path, thing_dir],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            while True:
                line = popen.stdout.readline()
                if '' == line:
                    break
                else:
                    self._log.info('%s', line)
            code = popen.wait()
            if 0 != code:
                self._log.error('failed to extract meshes; unified_mesh_hack terminated with code %d', code)
                raise InvalidThingException(job.path)
            else:
                self._log.debug('unified_mesh_hack terminated with code %d', code)
                stl_0_path = os.path.join(thing_dir, 'UNIFIED_MESH_HACK_0.stl')
                stl_1_path = os.path.join(thing_dir, 'UNIFIED_MESH_HACK_1.stl')
                if os.path.exists(stl_0_path) and os.path.exists(stl_1_path):
                    recipe = _DualThingRecipe(
                        self._server, self._config, job, stl_0_path, stl_1_path)
                    pass
                elif os.path.exists(stl_0_path):
                    recipe = _SingleThingRecipe(
                        self._server, self._config, job, stl_0_path)
                elif os.path.exists(stl_1_path):
                    recipe = _SingleThingRecipe(
                        self._server, self._config, job, stl_1_path)
                else:
                    raise InvalidThingException(job.path)
                return recipe


class Recipe(object):
    def __init__(self, server, config, job):
        self._config = config
        self._log = logging.getLogger(self.__class__.__name__)
        self._job = job
        self._server = server

    def getgcodeprocessors(self):
        gcodeprocessors = self._job.gcodeprocessor
        if None is gcodeprocessors:
            gcodeprocessors = []
        if (conveyor.domain.Slicer.SKEINFORGE == self._job.slicer_settings.slicer
            and 'Skeinforge50Processor' not in gcodeprocessors):
                gcodeprocessors.insert(0, 'Skeinforge50Processor')
        return gcodeprocessors

    def _slicertask(self, profile, inputpath, outputpath, with_start_end, slicer_config=None):
        if slicer_config is None:
            slicer_config = self._job.slicer_settings
        def runningcallback(task):
            self._log.info("slicing %s to %s" % (inputpath, outputpath))
            self._server.slice(
                profile, inputpath, outputpath, with_start_end,
                slicer_config, self._job.material, task)
        slicertask = conveyor.task.Task()
        slicertask.runningevent.attach(runningcallback)
        return slicertask

    def _gcodeprocessortask(self, inputpath, outputpath):
        factory = makerbot_driver.GcodeProcessors.ProcessorFactory()
        gcodeprocessor_list = self.getgcodeprocessors()
        gcodeprocessors = list(factory.get_processors(gcodeprocessor_list))
        def runningcallback(task):
            try:
                self._log.info('processing gcode %s -> %s', inputpath, outputpath)
                with open(inputpath) as f:
                    output = list(f)
                    for gcodeprocessor in gcodeprocessors:
                        output = gcodeprocessor.process_gcode(output)
                with open(outputpath, 'w') as f:
                    for line in output:
                        f.write(line)
            except Exception as e:
                self._log.debug('unhandled exception', exc_info=True)
                task.fail(e)
            else:
                task.end(None)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task

    def _dualstrusiontask(self, tool_0_path, tool_1_path, outputpath):
        def runningcallback(task):
            self._log.info("weaving together %s and %s to %s for dualstrusion" % (tool_0_path, tool_1_path, outputpath))
            try:
                with contextlib.nested(open(tool_0_path), open(tool_1_path)) as (t0, t1):
                    t0_codes = conveyor.dualstrusion.GcodeObject(list(t0))
                    t1_codes = conveyor.dualstrusion.GcodeObject(list(t1))
                weaver = conveyor.dualstrusion.DualstrusionWeaver(t0_codes, t1_codes)
                output = weaver.combine_codes()
                with open(outputpath, 'w') as f:
                    for line in output:
                        f.write(line)
            except Exception as e:
                self._log.debug("unhandled exception", exec_info=true)
                task.fail(e)
            else:
                task.end(None)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task

    def _printtask(self, printerthread, inputpath, dualstrusion):
        def runningcallback(task):
            self._log.info("printing %s" % (inputpath))
            printerthread.print(
                self._job, self._job.build_name, inputpath,
                self._job.skip_start_end, self._job.slicer_settings,
                self._job.print_to_file_type, self._job.material, task,
                dualstrusion)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task

    def _printtofiletask(self, profile, inputpath, outputpath, dualstrusion):
        def runningcallback(task):
            self._server.printtofile(
                profile, self._job.build_name, inputpath, outputpath,
                self._job.skip_start_end,  self._job.slicer_settings,
                self._job.print_to_file_type, self._job.material, task,
                dualstrusion)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task

    def print(self, printerthread):
        raise NotImplementedError

    def printtofile(self, profile, outputpath):
        raise NotImplementedError

    def slice(self, profile, outputpath):
        raise NotImplementedError


class _GcodeRecipe(Recipe):
    def __init__(self, server, config, job, gcodepath):
        Recipe.__init__(self, server, config, job)
        self._gcodepath = gcodepath

    def print(self, printerthread):
        tasks = []

        # Process Gcode
        gcodeprocessors = self.getgcodeprocessors()
        if 0 == len(gcodeprocessors):
            processed_gcodepath = self._job.path
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as processed_gcodefp:
                processed_gcodepath = processed_gcodefp.name
            gcodeprocessortask = self._gcodeprocessortask(
                self._job.path, processed_gcodepath)
            tasks.append(gcodeprocessortask)

        # Print
        printtask = self._printtask(printerthread, processed_gcodepath, False)
        tasks.append(printtask)

        def process_endcallback(task):
            if processed_gcodepath != self._gcodepath:
                os.unlink(processed_gcodepath)
        process = conveyor.process.tasksequence(self._job, tasks)
        process.endevent.attach(process_endcallback)
        return process


    def printtofile(self, profile, outputpath):
        tasks = []

        # Process Gcode
        gcodeprocessors = self.getgcodeprocessors()
        if 0 == len(gcodeprocessors):
            processed_gcodepath = self._job.path
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as processed_gcodefp:
                processed_gcodepath = processed_gcodefp.name
            gcodeprocessortask = self._gcodeprocessortask(
                self._job.path, processed_gcodepath)
            tasks.append(gcodeprocessortask)

        # Print
        printtofiletask = self._printtofiletask(
            profile, processed_gcodepath, outputpath, False)
        tasks.append(printtofiletask)

        def process_endcallback(task):
            if processed_gcodepath != self._gcoepath:
                os.unlink(processed_gcodepath)
        process = conveyor.process.tasksequence(self._job, tasks)
        process.endevent.attach(process_endcallback)
        return process


class _StlRecipe(Recipe):
    def __init__(self, server, config, job, stlpath):
        Recipe.__init__(self, server, config, job)
        self._stlpath = stlpath

    def print(self, printerthread):
        tasks = []

        # Slice
        with tempfile.NamedTemporaryFile(suffix='.gcode') as gcodefp:
            gcodepath = gcodefp.name
        profile = printerthread.getprofile()
        slicetask = self._slicertask(profile, self._stlpath, gcodepath, False)
        tasks.append(slicetask)

        # Process Gcode
        gcodeprocessors = self.getgcodeprocessors()
        if 0 == len(gcodeprocessors):
            processed_gcodepath = gcodepath
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as processed_gcodefp:
                processed_gcodepath = processed_gcodefp.name
            gcodeprocessortask = self._gcodeprocessortask(
                gcodepath, processed_gcodepath)
            tasks.append(gcodeprocessortask)

        # Print
        printtask = self._printtask(printerthread, processed_gcodepath, False)
        tasks.append(printtask)

        def process_endcallback(task):
            os.unlink(gcodepath)
            if gcodepath != processed_gcodepath:
                os.unlink(processed_gcodepath)
        process = conveyor.process.tasksequence(self._job, tasks)
        process.endevent.attach(process_endcallback)
        return process

    def printtofile(self, profile, outputpath):
        tasks = []

        # Slice
        with tempfile.NamedTemporaryFile(suffix='.gcode') as gcodefp:
            gcodepath = gcodefp.name
        slicetask = self._slicertask(profile, self._stlpath, gcodepath, False)
        tasks.append(slicetask)

        # Process Gcode
        gcodeprocessors = self.getgcodeprocessors()
        if 0 == len(gcodeprocessors):
            processed_gcodepath = gcodepath
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as processed_gcodefp:
                processed_gcodepath = processed_gcodefp.name
            gcodeprocessortask = self._gcodeprocessortask(
                gcodepath, processed_gcodepath)
            tasks.append(gcodeprocessortask)

        # Print
        printtofiletask = self._printtofiletask(
            profile, processed_gcodepath, outputpath, False)
        tasks.append(printtofiletask)

        def process_endcallback(task):
            os.unlink(gcodepath)
            if gcodepath != processed_gcodepath:
                os.unlink(processed_gcodepath)
        process = conveyor.process.tasksequence(self._job, tasks)
        process.endevent.attach(process_endcallback)
        return process

    def slice(self, profile, outputpath):
        tasks = []

        # Slice
        gcodeprocessors = self.getgcodeprocessors()
        if 0 == len(gcodeprocessors):
            gcodepath = outputpath
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as gcodefp:
                gcodepath = gcodefp.name
        slicetask = self._slicertask(
            profile, self._stlpath, gcodepath, self._job.with_start_end)
        tasks.append(slicetask)

        # Process Gcode
        if 0 != len(gcodeprocessors):
            gcodeprocessortask = self._gcodeprocessortask(gcodepath, outputpath)
            tasks.append(gcodeprocessortask)

        def process_endcallback(task):
            if gcodepath != outputpath:
                os.unlink(gcodepath)
        process = conveyor.process.tasksequence(self._job, tasks)
        process.endevent.attach(process_endcallback)
        return process


class _ThingRecipe(Recipe):
    pass


class _SingleThingRecipe(_ThingRecipe):
    def __init__(self, server, config, job, stl_path):
        _ThingRecipe.__init__(self, server, config, job)
        self._stl_path = stl_path

    def print(self, printerthread):
        stlrecipe = _StlRecipe(
            self._server, self._config, self._job, self._stl_path)
        process = stlrecipe.print(printerthread)
        return process

    def printtofile(self, profile, outputpath):
        stlrecipe = _StlRecipe(
            self._server, self._config, self._job, self._stl_path)
        process = stlrecipe.printtofile(profile, outputpath)
        return process

    def slice(self, profile, outputpath):
        stlrecipe = _StlRecipe(
            self._server, self._config, self._job, self._stl_path)
        process = stlrecipe.slice(profile, outputpath)
        return process


class _DualThingRecipe(_ThingRecipe):
    def __init__(self, server, config, job, stl_0_path, stl_1_path):
        _ThingRecipe.__init__(self, server, config, job)
        self._stl_0_path = stl_0_path
        self._stl_1_path = stl_1_path

    def printtofile(self, profile, outputpath):
        tasks = []
        stl_1_path = self._stl_1_path
        with tempfile.NamedTemporaryFile(suffix='.0.gcode') as f:
            gcode_0_path = f.name
        with tempfile.NamedTemporaryFile(suffix='.1.gcode') as f:
            gcode_1_path = f.name

        with_start_end = False

        settings_0 = conveyor.domain.SlicerConfiguration.fromdict(self._job.slicer_settings.todict())
        settings_0.extruder = '0'
        slice_0_task = self._slicertask(profile, self._stl_0_path, gcode_0_path, False, slicer_config=settings_0)
        tasks.append(slice_0_task)

        settings_1 = conveyor.domain.SlicerConfiguration.fromdict(self._job.slicer_settings.todict())
        settings_1.extruder = '1'
        slice_1_task = self._slicertask(profile, self._stl_1_path, gcode_1_path, False, slicer_config=settings_1)
        tasks.append(slice_1_task)

        #Combine for dualstrusion
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=True) as f:
            dualstrusion_path = f.name
        tasks.append(self._dualstrusiontask(gcode_0_path, gcode_1_path, dualstrusion_path))

        # Process Gcode
        gcodeprocessors = self.getgcodeprocessors()
        if 0 == len(gcodeprocessors):
            processed_gcodepath = dualstrusion_path
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as processed_gcodefp:
                processed_gcodepath = processed_gcodefp.name
            gcodeprocessortask = self._gcodeprocessortask(
                dualstrusion_path, processed_gcodepath)
            tasks.append(gcodeprocessortask)

        # Print To File
        printtofiletask = self._printtofiletask(
            profile, processed_gcodepath, outputpath, True)
        tasks.append(printtofiletask)

        process = conveyor.process.tasksequence(self._job, tasks)
        def process_endcallback(task):
            for path in [gcode_0_path, gcode_1_path, processed_gcodepath]:
                os.unlink(path)
        process.endevent.attach(process_endcallback)
        return process

    def slice(self, profile, outputpath):
        tasks = []
        with tempfile.NamedTemporaryFile(suffix='.0.gcode') as f:
            gcode_0_path = f.name
        with tempfile.NamedTemporaryFile(suffix='.1.gcode') as f:
            gcode_1_path = f.name

        with_start_end = False

        settings_0 = conveyor.domain.SlicerConfiguration.fromdict(self._job.slicer_settings.todict())
        settings_0.extruder = '0'
        slice_0_task = self._slicertask(profile, self._stl_0_path, gcode_0_path, False, slicer_config=settings_0)
        tasks.append(slice_0_task)

        settings_1 = conveyor.domain.SlicerConfiguration.fromdict(self._job.slicer_settings.todict())
        settings_1.extruder = '1'
        slice_1_task = self._slicertask(profile, self._stl_1_path, gcode_1_path, False, slicer_config=settings_1)
        tasks.append(slice_1_task)

        #Combine for dualstrusion
        with tempfile.NamedTemporaryFile(suffix='.gcode') as f:
            dualstrusion_path = f.name
        tasks.append(self._dualstrusiontask(gcode_0_path, gcode_1_path, dualstrusion_path))

        # Process Gcode
        gcodeprocessors = self.getgcodeprocessors()
        gcodeprocessortask = self._gcodeprocessortask(
            dualstrusion_path, outputpath)
        tasks.append(gcodeprocessortask)

        process = conveyor.process.tasksequence(self._job, tasks)
        def process_endcallback(task):
            for path in [gcode_0_path, gcode_1_path, dualstrusion_path]:
                os.unlink(path)
        process.endevent.attach(process_endcallback)
        return process

    def print(self, printerthread):
        profile = printerthread.getprofile()
        tasks = []
        with tempfile.NamedTemporaryFile(suffix='.0.gcode') as f:
            gcode_0_path = f.name
        with tempfile.NamedTemporaryFile(suffix='.1.gcode') as f:
            gcode_1_path = f.name

        with_start_end = False

        settings_0 = conveyor.domain.SlicerConfiguration.fromdict(self._job.slicer_settings.todict())
        settings_0.extruder = '0'
        slice_0_task = self._slicertask(profile, self._stl_0_path, gcode_0_path, False, slicer_config=settings_0)
        tasks.append(slice_0_task)

        settings_1 = conveyor.domain.SlicerConfiguration.fromdict(self._job.slicer_settings.todict())
        settings_1.extruder = '1'
        slice_1_task = self._slicertask(profile, self._stl_1_path, gcode_1_path, False, slicer_config=settings_1)
        tasks.append(slice_1_task)

        #Combine for dualstrusion
        with tempfile.NamedTemporaryFile(suffix='.gcode') as f:
            dualstrusion_path = f.name
        tasks.append(self._dualstrusiontask(gcode_0_path, gcode_1_path, dualstrusion_path))

        # Process Gcode
        gcodeprocessors = self.getgcodeprocessors()
        if 0 == len(gcodeprocessors):
            processed_gcodepath = dualstrusion_path
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as processed_gcodefp:
                processed_gcodepath = processed_gcodefp.name
            gcodeprocessortask = self._gcodeprocessortask(
                dualstrusion_path, processed_gcodepath)
            tasks.append(gcodeprocessortask)

        #print
        printtask = self._printtask(printerthread, processed_gcodepath, True)
        tasks.append(printtask)

        process = conveyor.process.tasksequence(self._job, tasks)
        def process_endcallback(task):
            for path in [gcode_0_path, gcode_1_path, dualstrusion_path, processed_gcodefp]:
                os.unlink(path)
        process.endevent.attach(process_endcallback)
        return process


class UnsupportedModelTypeException(Exception):
    def __init__(self, path):
        Exception.__init__(self, path)
        self.path = path


class MissingFileException(Exception):
    def __init__(self, path):
        Exception.__init__(self, path)
        self.path = path


class NotFileException(Exception):
    def __init__(self, path):
        Exception.__init__(self, path)
        self.path = path


class InvalidThingException(Exception):
    def __init__(self, path):
        Exception.__init__(self, path)
        self.path = path
