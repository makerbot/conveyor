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

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.enum
import conveyor.process
import conveyor.task
import conveyor.thing
import conveyor.printer.replicator
import conveyor.toolpath.miraclegrue
import conveyor.toolpath.skeinforge

class RecipeManager(object):
    def __init__(self, config):
        self._config = config

    def getrecipe(self, thing):
        if thing.endswith('.gcode'):
            recipe = self._getrecipe_gcode(thing)
        else:
            recipe = self._getrecipe_thing(thing)
        return recipe

    def _getrecipe_gcode(self, gcode):
        if not os.path.exists(gcode):
            raise Exception
        elif not os.path.isfile(gcode):
            raise Exception
        else:
            recipe = _GcodeRecipe(self._config, gcode)
            return recipe

    def _getrecipe_thing(self, thing):
        if not os.path.exists(thing):
            raise Exception
        elif not os.path.isdir(thing):
            raise Exception
        else:
            manifestpath = os.path.join(thing, 'manifest.json')
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

    def print(self):
        raise NotImplementedError

    def printtofile(self, s3g):
        raise NotImplementedError

    def slice(self, gcode):
        raise NotImplementedError

class _GcodeRecipe(Recipe):
    def __init__(self, config, gcode):
        Recipe.__init__(self, config)
        self._gcode = gcode

    def print(self):
        printer = conveyor.printer.replicator.ReplicatorPrinter()
        task = printer.print(self._gcode)
        return task

    def printtofile(self, s3gpath):
        printer = conveyor.printer.replicator.ReplicatorPrinter()
        task = printer.printtofile(self._gcode, s3gpath)
        return task

class _ThingRecipe(Recipe):
    def __init__(self, config, manifest):
        Recipe.__init__(self, config)
        self._manifest = manifest

    def _createtask(self, func):
        raise NotImplementedError

    def _gcodefilename(self, stl):
        gcode = ''.join((stl[:-4], '.gcode'))
        return gcode

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
        value = self._config['common']['slicer']
        if 'miraclegrue' == value:
            toolpath = conveyor.toolpath.miraclegrue.MiracleGrueToolpath()
        elif 'skeinforge' == value:
            toolpath = conveyor.toolpath.skeinforge.SkeinforgeToolpath()
        else:
            raise ValueError(value)
        instance = self._getinstance_a()
        objectpath = os.path.join(self._manifest.base, instance.object.name)
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as gcodefp:
            pass
        gcodepath = gcodefp.name
        os.unlink(gcodepath)
        task1 = toolpath.generate(objectpath, gcodepath)
        printer = conveyor.printer.replicator.ReplicatorPrinter()
        task2 = printer.print(gcodepath)
        def endcallback(task):
            os.unlink(gcodepath)
        task = conveyor.process.tasksequence([task1, task2])
        task.endevent.attach(endcallback)
        return task

    def printtofile(self, s3gpath):
        value = self._config['common']['slicer']
        if 'miraclegrue' == value:
            toolpath = conveyor.toolpath.miraclegrue.MiracleGrueToolpath()
        elif 'skeinforge' == value:
            toolpath = conveyor.toolpath.skeinforge.SkeinforgeToolpath()
        else:
            raise ValueError(value)
        instance = self._getinstance_a()
        objectpath = os.path.join(self._manifest.base, instance.object.name)
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as gcodefp:
            pass
        gcodepath = gcodefp.name
        os.unlink(gcodepath)
        task1 = toolpath.generate(objectpath, gcodepath)
        printer = conveyor.printer.replicator.ReplicatorPrinter()
        task2 = printer.printtofile(gcodepath, s3gpath)
        def endcallback(task):
            os.unlink(gcodepath)
        task = conveyor.process.tasksequence([task1, task2])
        task.endevent.attach(endcallback)
        return task

    def slice(self, gcodepath):
        value = self._config['common']['slicer']
        if 'miraclegrue' == value:
            toolpath = conveyor.toolpath.miraclegrue.MiracleGrueToolpath()
        elif 'skeinforge' == value:
            toolpath = conveyor.toolpath.skeinforge.SkeinforgeToolpath()
        else:
            raise ValueError(value)
        instance = self._getinstance_a()
        objectpath = os.path.join(self._manifest.base, instance.object.name)
        task = toolpath.generate(objectpath, gcodepath)
        return task

class _DualThingRecipe(_ThingRecipe):
    pass
