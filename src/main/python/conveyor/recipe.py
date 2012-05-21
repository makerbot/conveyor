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

import conveyor.process
import conveyor.task
import conveyor.thing
import conveyor.toolpath.skeinforge

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

    def _createtask(self, func):
        raise NotImplementedError

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

    def print(self):
        def func(printer, inputpath):
            task = printer.build(inputpath)
            return task
        task = self._createtask(func)
        return task

    def printtofile(self, s3g):
        def func(printer, inputpath):
            outputpath = os.path.abspath(s3g)
            task = printer.buildtofile(inputpath, outputpath)
            return task
        task = self._createtask(func)
        return task

class _SingleRecipe(Recipe):
    pass

class _DualRecipe(Recipe):
    pass
