# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
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

import makerbot_driver
import os
import os.path
import tempfile
import zipfile

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.domain
import conveyor.enum
import conveyor.printer.s3g
import conveyor.process
import conveyor.task
import conveyor.thing
import conveyor.toolpath.miraclegrue
import conveyor.toolpath.skeinforge

class RecipeManager(object):
    def __init__(self, server, config):
        self._config = config
        self._server = server

    def getrecipe(self, job):
        root, ext = os.path.splitext(job.path)
        if '.gcode' == ext.lower():
            recipe = self._getrecipe_gcode(job)
        elif '.stl' == ext.lower():
            recipe = self._getrecipe_stl(job)
        elif '.thing' == ext.lower():
            recipe = self._getrecipe_thing(job)
        else:
            #assuming a malformed thing. Print an error here someday
            recipe = self._getrecipe_thing(job)
        return recipe

    def _getrecipe_gcode(self, job):
        if not os.path.exists(job.path):
            raise Exception
        elif not os.path.isfile(job.path):
            raise Exception
        else:
            recipe = _GcodeRecipe(self._server, self._config, job)
        return recipe

    def _getrecipe_stl(self, job):
        if not os.path.exists(job.path):
            raise Exception
        elif not os.path.isfile(job.path):
            raise Exception
        else:
            recipe = _StlRecipe(self._server, self._config, job, job.path)
            return recipe

    def _getrecipe_thing(self, job):
        if not os.path.exists(job.path):
            raise Exception
        else:
            if not os.path.isdir(job.path):
                recipe = self._getrecipe_thing_zip(job)
            else:
                recipe = self._getrecipe_thing_dir(job, job.path)
            return recipe

    def _getrecipe_thing_zip(self, job):
        directory = tempfile.mkdtemp()
        with zipfile.ZipFile(job.path, 'r') as zip:
            zip.extractall(directory)
        recipe = self._getrecipe_thing_dir(job, directory)
        return recipe

    def _getrecipe_thing_dir(self, job, directory):
        if not os.path.isdir(directory):
            raise Exception
        else:
            manifestpath = os.path.join(directory, 'manifest.json')
            if not os.path.exists(manifestpath):
                raise Exception
            else:
                manifest = conveyor.thing.Manifest.frompath(manifestpath)
                manifest.validate()
                if None is not manifest.unified_mesh_hack:
                    stlpath = os.path.join(
                        manifest.base, manifest.unified_mesh_hack)
                    recipe = _StlRecipe(
                        self._server, self._config, job, stlpath)
                elif 1 == len(manifest.instances):
                    recipe = _SingleThingRecipe(
                        self._server, self._config, job, manifest)
                elif 2 == len(manifest.instances):
                    recipe = _DualThingRecipe(
                        self._server, self._config, job, manifest)
                else:
                    raise Exception
                return recipe

class Recipe(object):
    def __init__(self, server, config, job):
        self._config = config
        self._job = job
        self._server = server

    def _slicetask(self, profile, inputpath, outputpath, with_start_end):
        def runningcallback(task):
            self._server.slice(
                profile, inputpath, outputpath, with_start_end, material, task)
        toolpathtask = conveyor.task.Task()
        toolpathtask.runningevent.attach(runningcallback)
        return toolpathtask

    def _preprocessortask(self, inputpath, outputpath):
        def runningcallback(task):
            try:
                # TODO: this is totally wrong because 'preprocessor' is a
                # string at this point.
                self._job.preprocessor.process_file(inputpath, outputpath)
            except Exception as e:
                task.fail(e)
            else:
                task.end(None)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task

    def _printtask(self, printerthread, inputpath):
        def runningcallback(task):
            printerthread.print(
                self._job, self._job.build_name, inputpath,
                self._job.skip_start_end, self._job.material, task)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task

    def _printtofiletask(self, profile, inputpath, outputpath):
            def runningcallback(task):
                self._server.printtofile(
                    profile, self._job.build_name, inputpath, outputpath,
                    self._job.skip_start_end, self._job.material, task)
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
    def print(self, printerthread):
        tasks = []

        # Preprocess
        if not self._job.preprocessor:
            processed_gcodepath = self._job.path
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as processed_gcodefp:
                processed_gcodepath = processed_gcodefp.name
            preprocessortask = self._preprocessortask(
                self._path, processed_gcodepath)
            tasks.append(preprocessortask)

        # Print
        printtask = self._printtask(printerthread, processed_gcodepath)
        tasks.append(printtask)

        def process_endcallback(task):
            if processed_gcodepath != self._job.path:
                os.unlink(processed_gcodepath)
        process = conveyor.process.tasksequence(self._job, tasks)
        process.endevent.attach(process_endcallback)
        return process

    def printtofile(self, profile, outputpath):
        tasks = []

        # Preprocess
        if not self._job.preprocessor:
            processed_gcodepath = self._job.path
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as processed_gcodefp:
                processed_gcodepath = processed_gcodefp.name
            preprocessortask = self._preprocessortask(
                self._path, processed_gcodepath)
            tasks.append(preprocessortask)

        # Print
        printtofiletask = self._printtofiletask(
            profile, processed_gcodepath, outputpath)
        tasks.append(printtofiletask)

        def process_endcallback(task):
            if processed_gcodepath != self._job.path:
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
        slicetask = self._slicetask(profile, self._stlpath, gcodepath, False)
        tasks.append(slicetask)

        # Preprocess
        if not self._job.preprocessor:
            processed_gcodepath = gcodepath
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as processed_gcodefp:
                processed_gcodepath = processed_gcodefp.name
            preprocessortask = self._preprocessortask(
                gcodepath, processed_gcodepath)
            tasks.append(preprocessortask)

        # Print
        printtask = self._printtask(printerthread, processed_gcodepath)
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
        slicetask = self._slicetask(profile, self._stlpath, gcodepath, False)
        tasks.append(slicetask)

        # Preprocess
        if not self._job.preprocessor:
            processed_gcodepath = gcodepath
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as processed_gcodefp:
                processed_gcodepath = processed_gcodefp.name
            preprocessortask = self._preprocessortask(
                gcodepath, processed_gcodepath)
            tasks.append(preprocessortask)

        # Print
        printtofiletask = self._printtofiletask(
            profile, processed_gcodepath, outputpath)
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
        if not self._job.preprocessor:
            gcodepath = outputpath
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as gcodefp:
                gcodepath = gcodefp.name
        slicetask = self._slicetask(
            profile, self._stlpath, gcodepath, self._job.with_start_end)
        tasks.append(slicetask)

        # Preprocess
        if self._job.preprocessor:
            preprocessortask = self._preprocessortask(gcodepath, outputpath)
            tasks.append(preprocessortask)

        def process_endcallback(task):
            if gcodepath != outputpath:
                os.unlink(gcodepath)
        process = conveyor.process.tasksequence(self._job, tasks)
        process.endevent.attach(process_endcallback)
        return process

class _ThingRecipe(Recipe):
    def __init__(self, server, config, job, manifest):
        Recipe.__init__(self, server, config, job)
        self._manifest = manifest

    def _getinstance(self, name):
        for instance in self._manifest.instances.itervalues():
            if name == instance.construction.name:
                return instance
        raise Exception

    def _getinstance_a(self):
        instance = self._getinstance('plastic A')
        return instance

    def _getinstance_b(self):
        instance = self._getinstance('plastic B')
        return instance

class _SingleThingRecipe(_ThingRecipe):
    def print(self, printerthread):
        instance = self._getinstance_a()
        objectpath = os.path.join(self._manifest.base, instance.object.name)
        stlrecipe = _StlRecipe(
            self._server, self._config, self._job, objectpath)
        process = stlrecipe.print(printerthread)
        return process

    def printtofile(self, profile, outputpath):
        instance = self._getinstance_a()
        objectpath = os.path.join(self._manifest.base, instance.object.name)
        stlrecipe = _StlRecipe(
            self._server, self._config, self._job, objectpath)
        process = stlrecipe.printtofile(profile, outputpath)
        return process

    def slice(self, profile, outputpath):
        instance = self._getinstance_a()
        objectpath = os.path.join(self._manifest.base, instance.object.name)
        stlrecipe = _StlRecipe(
            self._server, self._config, self._job, objectpath)
        process = stlrecipe.slice(profile, outputpath)
        return process

class _DualThingRecipe(_ThingRecipe):
    pass
