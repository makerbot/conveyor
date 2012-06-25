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

import os
import os.path
import tempfile
import zipfile

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.enum
import conveyor.process
import conveyor.task
import conveyor.thing
import conveyor.printer.s3g
import conveyor.toolpath.miraclegrue
import conveyor.toolpath.skeinforge
import s3g

class RecipeManager(object):
    def __init__(self, config):
        self._config = config

    def getrecipe(self, path):
        root, ext = os.path.splitext(path)
        if '.gcode' == ext:
            recipe = self._getrecipe_gcode(path)
        elif '.stl' == ext:
            recipe = self._getrecipe_stl(path)
        else:
            recipe = self._getrecipe_thing(path)
        return recipe

    def _getrecipe_gcode(self, path):
        if not os.path.exists(path):
            raise Exception
        elif not os.path.isfile(path):
            raise Exception
        else:
            recipe = _GcodeRecipe(self._config, path)
            return recipe

    def _getrecipe_stl(self, path):
        if not os.path.exists(path):
            raise Exception
        elif not os.path.isfile(path):
            raise Exception
        else:
            recipe = _StlRecipe(self._config, path)
            return recipe

    def _getrecipe_thing(self, path):
        if not os.path.exists(path):
            raise Exception
        else:
            if not os.path.isdir(path):
                recipe = self._getrecipe_thing_zip(path)
            else:
                recipe = self._getrecipe_thing_dir(path)
            return recipe

    def _getrecipe_thing_zip(self, path):
        directory = tempfile.mkdtemp()
        with zipfile.ZipFile(path, 'r') as zip:
            zip.extractall(directory)
        recipe = self._getrecipe_thing_dir(directory)
        return recipe

    def _getrecipe_thing_dir(self, path):
        if not os.path.isdir(path):
            raise Exception
        else:
            manifestpath = os.path.join(path, 'manifest.json')
            if not os.path.exists(manifestpath):
                raise Exception
            else:
                manifest = conveyor.thing.Manifest.frompath(manifestpath)
                manifest.validate()
                if 1 == len(manifest.instances):
                    recipe = _SingleThingRecipe(self._config, manifest)
                elif 2 == len(manifest.instances):
                    recipe = _DualThingRecipe(self._config, manifest)
                else:
                    raise Exception
                return recipe

class Recipe(object):
    def __init__(self, config):
        self._config = config

    def _createtoolpath(self):
        slicer = self._config['common']['slicer']
        if 'miraclegrue' == slicer:
            toolpath = conveyor.toolpath.miraclegrue.MiracleGrueToolpath()
        elif 'skeinforge' == slicer:
            toolpath = conveyor.toolpath.skeinforge.SkeinforgeToolpath()
        else:
            raise ValueError(slicer)
        return toolpath

    def _createprinter(self):
        serialport = self._config['common']['serialport']
        profilename = self._config['common']['profile']
        profile = s3g.Profile(profilename)
        baudrate = profile.values['baudrate']
        printer = conveyor.printer.s3g.S3gPrinter(
            profile, serialport, baudrate)
        return printer

    def print(self, skip_start_end=False):
        raise NotImplementedError

    def printtofile(self, s3g, skip_start_end=False):
        raise NotImplementedError

    def slice(self, gcode):
        raise NotImplementedError

class _GcodeRecipe(Recipe):
    def __init__(self, config, path):
        Recipe.__init__(self, config)
        self._path = path

    def print(self, skip_start_end):
        printer = self._createprinter()
        task = printer.print(self._path, skip_start_end)
        return task

    def printtofile(self, s3gpath, skip_start_end):
        printer = self._createprinter()
        task = printer.printtofile(self._path, s3gpath, skip_start_end)
        return task

# TODO: share code between _StlRecipe and _SingleThingRecipe.

class _StlRecipe(Recipe):
    def __init__(self, config, path):
        Recipe.__init__(self, config)
        self._path = path

    def print(self, skip_start_end):
        toolpath = self._createtoolpath()
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as gcodefp:
            pass
        gcodepath = gcodefp.name
        os.unlink(gcodepath)
        task1 = toolpath.generate(self._path, gcodepath)
        printer = self._createprinter()
        task2 = printer.print(gcodepath)
        def endcallback(task):
            os.unlink(gcodepath)
        task = conveyor.process.tasksequence([task1, task2])
        task.endevent.attach(endcallback)
        return task

    def printtofile(self, s3gpath):
        toolpath = self._createtoolpath()
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as gcodefp:
            pass
        gcodepath = gcodefp.name
        os.unlink(gcodepath)
        task1 = toolpath.generate(self._path, gcodepath)
        printer = self._createprinter()
        task2 = printer.printtofile(gcodepath, s3gpath)
        def endcallback(task):
            os.unlink(gcodepath)
        task = conveyor.process.tasksequence([task1, task2])
        task.endevent.attach(endcallback)
        return task

    def slice(self, gcodepath, with_start_end):
        print('recipe 193 gcodepath=%r', gcodepath)
        toolpath = self._createtoolpath()
        if with_start_end:
            printer = self._createprinter()
            task = toolpath.generate(self._path, gcodepath, with_start_end, printer)

        else:
            task = toolpath.generate(self._path, gcodepath, with_start_end)
        return task

class _ThingRecipe(Recipe):
    def __init__(self, config, manifest):
        Recipe.__init__(self, config)
        self._manifest = manifest

    def _createtask(self, func):
        raise NotImplementedError

    def _gcodefilename(self, path):
        root, ext = os.path.splitext(path)
        result = ''.join((root, '.gcode'))
        return result

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

    def _faketask(self):
        def runningcallback(task):
            task.end(None)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task

    def print(self):
        task = self._faketask()
        return task

    def printtofile(self, s3gpath):
        task = self._faketask()
        return task

class _SingleThingRecipe(_ThingRecipe):
    def print(self):
        toolpath = self._createtoolpath()
        instance = self._getinstance_a()
        objectpath = os.path.join(self._manifest.base, instance.object.name)
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as gcodefp:
            pass
        gcodepath = gcodefp.name
        os.unlink(gcodepath)
        task1 = toolpath.generate(objectpath, gcodepath)
        printer = self._createprinter()
        task2 = printer.print(gcodepath)
        def endcallback(task):
            os.unlink(gcodepath)
        task = conveyor.process.tasksequence([task1, task2])
        task.endevent.attach(endcallback)
        return task

    def printtofile(self, s3gpath):
        toolpath = self._createtoolpath()
        instance = self._getinstance_a()
        objectpath = os.path.join(self._manifest.base, instance.object.name)
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as gcodefp:
            pass
        gcodepath = gcodefp.name
        os.unlink(gcodepath)
        task1 = toolpath.generate(objectpath, gcodepath)
        printer = self._createprinter()
        task2 = printer.printtofile(gcodepath, s3gpath)
        def endcallback(task):
            os.unlink(gcodepath)
        task = conveyor.process.tasksequence([task1, task2])
        task.endevent.attach(endcallback)
        return task

    def slice(self, gcodepath, with_start_end):
        print('recipe 277 gcodepath=%r', gcodepath)

        toolpath = self._createtoolpath()
        instance = self._getinstance_a()
        objectpath = os.path.join(self._manifest.base, instance.object.name)
        if with_start_end:
            printer = self._createprinter()
            task = toolpath.generate(self._path, gcodepath, with_start_end, printer)
        else:
            task = toolpath.generate(self._path, gcodepath, with_start_end)
        return task

class _DualThingRecipe(_ThingRecipe):
    pass
