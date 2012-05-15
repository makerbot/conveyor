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

import dbus
import dbus.mainloop.qt
import os
import os.path
import tempfile

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.printer.dbus
import conveyor.process
import conveyor.task
import conveyor.thing
import conveyor.toolpathgenerator.dbus

dbus.mainloop.qt.DBusQtMainLoop(set_as_default=True)

class RecipeManager(object):
    def getrecipe(self, thing):
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
                    recipe = _SingleRecipe(manifest)
                elif 2 == len(manifest.instances):
                    recipe = _DualRecipe(manifest)
                else:
                    raise Exception
                return recipe

class Recipe(object):
    def __init__(self, manifest):
        self._manifest = manifest

    def _gcodefilename(self, stl):
        gcode = ''.join((stl[:-4], '.gcode'))
        return gcode

    def _getinstance(self, manifest, name):
        for instance in manifest.instances.itervalues():
            if name == instance.construction.name:
                return instance
        raise Exception

    def _getinstance_a(self, manifest):
        instance = self._getinstance(manifest, 'plastic A')
        return instance

    def _getinstance_b(self, manifest):
        instance = self._getinstance(manifest, 'plastic B')
        return instance

    def print(self, toolpathgeneratorbusname, printerbusname):
        def func(printer, inputpath):
            task = printer.build(inputpath)
            return task
        task = self._createtask(toolpathgeneratorbusname, printerbusname, func)
        return task

    def printtofile(self, toolpathgeneratorbusname, printerbusname, s3g):
        def func(printer, inputpath):
            outputpath = os.path.abspath(s3g)
            task = printer.buildtofile(inputpath, outputpath)
            return task
        task = self._createtask(toolpathgeneratorbusname, printerbusname, func)
        return task

class _SingleRecipe(Recipe):
    def _createtask(self, toolpathgeneratorbusname, printerbusname, func):
        bus = dbus.Sessionbus()
        toolpathgenerator = conveyor.toolpathgenerator.dbus._DbusToolpathGenerator.create(
            bus, toolpathgeneratorbusname)
        printer = conveyor.printer.dbus._DbusPrinter.create(
            bus, printerbusname)
        instance = self._getinstance_a(self._manifest)
        stl = os.path.abspath(os.path.join(self._manifest.base, instance.object.name))
        assert stl.endswith('.stl')
        gcode = self._gcodefilename(stl)
        task1 = toolpathgenerator.stl_to_gcode(stl)
        task2 = func(printer, gcode)
        tasks = [task1, task2]
        task = conveyor.process.tasksequence(tasks)
        return task

class _DualRecipe(Recipe):
    def _createtask(self, toolpathgeneratorbusname, printerbusname, func):
        bus = dbus.SessionBus()
        toolpathgenerator = conveyor.toolpathgenerator.dbus._DbusToolpathGenerator.create(
            bus, toolpathgeneratorbusname)
        printer = conveyor.printer.dbus._DbusPrinter.create(
            bus, printerbusname)
        instance_a = self._getinstance_a(self._manifest)
        instance_b = self._getinstance_b(self._manifest)
        stl_a = os.path.abspath(os.path.join(self._manifest.base, instance_a.object.name))
        stl_b = os.path.abspath(os.path.join(self._manifest.base, instance_b.object.name))
        assert stl_a.endswith('.stl')
        assert stl_b.endswith('.stl')
        gcode_a = self._gcodefilename(stl_a)
        gcode_b = self._gcodefilename(stl_b)
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as tmp:
            gcode_merged = tmp.name
        os.unlink(gcode_merged)
        task1 = toolpathgenerator.stl_to_gcode(stl_a)
        task2 = toolpathgenerator.stl_to_gcode(stl_b)
        task3 = toolpathgenerator.merge_gcode(gcode_a, gcode_b, gcode_merged)
        task4 = func(printer, gcode_merged)
        tasks = [task1, task2, task3, task4]
        task = conveyor.process.tasksequence(tasks)
        return task
