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
import makerbot_driver

class RecipeManager(object):
    def __init__(self, config):
        self._config = config

    def getrecipe(self, path, preprocessor):
        root, ext = os.path.splitext(path)
        if '.gcode' == ext.lower():
            recipe = self._getrecipe_gcode(path, preprocessor)
        elif '.stl' == ext.lower():
            recipe = self._getrecipe_stl(path, preprocessor)
        elif '.thing' == ext.lower():
            recipe = self._getrecipe_thing(path, preprocessor)
        else:
            #assuming a malformed thing. Print an error here someday
            recipe = self._getrecipe_thing(path, preprocessor)
        return recipe

    def _getrecipe_gcode(self, path, preprocessor):
        if not os.path.exists(path):
            raise Exception
        elif not os.path.isfile(path):
            raise Exception
        else:
            recipe = _GcodeRecipe(self._config, path, preprocessor)
        return recipe

    def _getrecipe_stl(self, path, preprocessor):
        if not os.path.exists(path):
            raise Exception
        elif not os.path.isfile(path):
            raise Exception
        else:
            recipe = _StlRecipe(self._config, path, preprocessor)
            return recipe

    def _getrecipe_thing(self, path, preprocessor):
        if not os.path.exists(path):
            raise Exception
        else:
            if not os.path.isdir(path):
                recipe = self._getrecipe_thing_zip(path, preprocessor)
            else:
                recipe = self._getrecipe_thing_dir(path, preprocessor)
            return recipe

    def _getrecipe_thing_zip(self, path, preprocessor):
        directory = tempfile.mkdtemp()
        with zipfile.ZipFile(path, 'r') as zip:
            zip.extractall(directory)
        recipe = self._getrecipe_thing_dir(directory, preprocessor)
        return recipe

    def _getrecipe_thing_dir(self, path, preprocessor):
        if not os.path.isdir(path):
            raise Exception
        else:
            manifestpath = os.path.join(path, 'manifest.json')
            if not os.path.exists(manifestpath):
                raise Exception
            else:
                manifest = conveyor.thing.Manifest.frompath(manifestpath)
                manifest.validate()
                if None is not manifest.unified_mesh_hack:
                    stlpath = os.path.join(manifest.base, manifest.unified_mesh_hack)
                    recipe = _StlRecipe(self._config, stlpath, preprocessor)
                elif 1 == len(manifest.instances):
                    recipe = _SingleThingRecipe(self._config, manifest, preprocessor)
                elif 2 == len(manifest.material_types()):
                    recipe = _DualThingRecipe(self._config, manifest, preprocessor)
                else:
                    raise Exception
                return recipe

class Recipe(object):
    def __init__(self, config, preprocessor):
        self._config = config
        self.preprocessor = preprocessor

    def _createtoolpath(self):
        slicer = self._config['common']['slicer']
        if 'miraclegrue' == slicer:
            configuration = conveyor.toolpath.miraclegrue.MiracleGrueConfiguration()
            configuration.miraclegruepath = self._config['miraclegrue']['path']
            configuration.miracleconfigpath = self._config['miraclegrue']['config']
            toolpath = conveyor.toolpath.miraclegrue.MiracleGrueToolpath(configuration)
        elif 'skeinforge' == slicer:
            configuration = conveyor.toolpath.skeinforge.SkeinforgeConfiguration()
            configuration.skeinforgepath = self._config['skeinforge']['path']
            configuration.profile = self._config['skeinforge']['profile']
            toolpath = conveyor.toolpath.skeinforge.SkeinforgeToolpath(configuration)
        else:
            raise ValueError(slicer)
        return toolpath

    def _createprinter(self, ep_name = None):
        """ create printer by specified endpoint
        @ep_name: named endpoint.ie '/dev/ttyX' or 'COMY' . None to create an endpoint based on config file value:
        """
        serialport = ep_name if ep_name else self._config['common']['serialport']
        profilename = self._config['common']['profile']
        profiledir = self._config['common']['profiledir']
        profile = makerbot_driver.Profile(profilename, profiledir)
        baudrate = profile.values['baudrate']
        import pdb
        pdb.set_trace()
        printer = conveyor.printer.s3g.S3gPrinter(
            profile, serialport, baudrate)
        return printer

    def print(self, skip_start_end):
        raise NotImplementedError

    def printtofile(self, s3g, skip_start_end):
        raise NotImplementedError

    def slice(self, gcode, with_start_end):
        raise NotImplementedError
    

class _GcodeRecipe(Recipe):
    def __init__(self, config, path, preprocessor):
        Recipe.__init__(self, config, preprocessor)
        self._path = path

    def print(self, skip_start_end, endpoint=None):
        tasks = []
        printer = self._createprinter(endpoint)
        if not self.preprocessor: 
            processed_gcodepath = self._path
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as processed_gcodefp:
                pass
            processed_gcodepath = processed_gcodefp.name
            os.unlink(processed_gcodepath)
            tasks.append(self.preprocessor.process_file(self._path, processed_gcodepath))
        tasks.append(printer.print(processed_gcodepath, skip_start_end))
        task = conveyor.process.tasksequence(tasks)
        return task

# TODO: share code between _StlRecipe and _SingleThingRecipe.

class _StlRecipe(Recipe):
    def __init__(self, config, path, preprocessor):
        Recipe.__init__(self, config, preprocessor)
        self._path = path

    def print(self, skip_start_end, endpoint=None):
        tasks = []
        toolpath = self._createtoolpath()
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as gcodefp:
            pass
        gcodepath = gcodefp.name
        os.unlink(gcodepath)
		import pdb
		pdb.set_trace()
        printer = self._createprinter(endpoint)
        tasks.append(toolpath.generate(self._path, gcodepath, False, printer))
        if not self.preprocessor:
            processed_gcodepath = gcodepath
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as processed_gcodefp:
                pass
            processed_gcodepath = processed_gcodefp.name
            os.unlink(processed_gcodepath)
            tasks.append(self.preprocessor.process_file(gcodepathff, processed_gcodepath))
        tasks.append(printer.print(processed_gcodepath, skip_start_end))
        def endcallback(task):
            os.unlink(gcodepath)
        task = conveyor.process.tasksequence(tasks)
        task.endevent.attach(endcallback)
        return task

    def printtofile(self, s3gpath, skip_start_end):
        tasks = []
        toolpath = self._createtoolpath()
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as gcodefp:
            pass
        gcodepath = gcodefp.name
        os.unlink(gcodepath)
        printer = self._createprinter()
        tasks.append(toolpath.generate(self._path, gcodepath, False, printer))
        if not self.preprocessor:
            processed_gcodepath = gcodepath
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as processed_gcodefp:
                pass
            processed_gcodepath = processed_gcodefp.name
            os.unlink(processed_gcodepath)
            tasks.append(self.preprocessor.process_file(gcodepath, processed_gcodepath))
        tasks.append(printer.printtofile(processed_gcodepath, s3gpath, skip_start_end))
        def endcallback(task):
            os.unlink(processed_gcodepath)
        task = conveyor.process.tasksequence(tasks)
        task.endevent.attach(endcallback)
        return task

    def slice(self, gcodepath, with_start_end):
        tasks = []
        toolpath = self._createtoolpath()
        printer = self._createprinter()
        tasks.append(toolpath.generate(self._path, gcodepath, with_start_end, printer))
        if not self.preprocessor:
            processed_gcodepath = gcodepath
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as processed_gcodefp:
                pass
            processed_gcodepath = processed_gcodefp.name
            os.unlink(processed_gcodepath)
            tasks.append(self.preprocessor.process_file(gcodepath, processed_gcodepath))
        task = conveyor.process.tasksequence(tasks)
        return task

class _ThingRecipe(Recipe):
    def __init__(self, config, manifest, preprocessor):
        Recipe.__init__(self, config, preprocessor)
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

    def print(self, skip_start_end):
        task = self._faketask()
        return task

    def printtofile(self, s3gpath, skip_start_end):
        task = self._faketask()
        return task

class _SingleThingRecipe(_ThingRecipe):


    def print(self, skip_start_end, endpoint=None):
        tasks = []
        toolpath = self._createtoolpath()
        instance = self._getinstance_a()
        objectpath = os.path.join(self._manifest.base, instance.object.name)
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as gcodefp:
            pass
        gcodepath = gcodefp.name
        os.unlink(gcodepath)
        printer = self._createprinter(endpoint)
        tasks.append(toolpath.generate(objectpath, gcodepath, False, printer))
        if not self.preprocessor:
            processed_gcodepath = gcodepath
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as processed_gcodefp:
                pass
            processed_gcodepath = processed_gcodefp.name
            os.unlink(processed_gcodepath)
            tasks.append(self.preprocessor.process_file(gcodepath, processed_gcodepath))
        tasks.append(printer.print(processed_gcodepath, skip_start_end))
        def endcallback(task):
            os.unlink(gcodepath)
        task = conveyor.process.tasksequence(tasks)
        task.endevent.attach(endcallback)
        return task

    def printtofile(self, s3gpath, skip_start_end):
        tasks = []
        toolpath = self._createtoolpath()
        instance = self._getinstance_a()
        objectpath = os.path.join(self._manifest.base, instance.object.name)
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as gcodefp:
            pass
        gcodepath = gcodefp.name
        os.unlink(gcodepath)
        printer = self._createprinter()
        tasks.append(toolpath.generate(objectpath, gcodepath, False, printer))
        if not self.preprocessor:
            processed_gcodepath = gcodepath
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as processed_gcodefp:
                pass
            processed_gcodepath = processed_gcodefp.name
            os.unlink(processed_gcodepath)
            tasks.append(self.preprocessor.process_file(gcodepath, processed_gcodepath))
        tasks.append(printer.printtofile(processed_gcodepath, s3gpath, skip_start_end))
        def endcallback(task):
            os.unlink(gcodepath)
        task = conveyor.process.tasksequence(tasks)
        task.endevent.attach(endcallback)
        return task

    def slice(self, gcodepath, with_start_end):
        tasks = []
        toolpath = self._createtoolpath()
        instance = self._getinstance_a()
        objectpath = os.path.join(self._manifest.base, instance.object.name)
        printer = self._createprinter()
        tasks.append(toolpath.generate(objectpath, gcodepath, with_start_end, printer))
        if not self.preprocessor:
            processed_gcodepath = gcodepath
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as processed_gcodefp:
                pass
            processed_gcodepath = processed_gcodefp.name
            os.unlink(processed_gcodepath)
            tasks.append(self.preprocessor.process_file(gcodepath, processed_gcodepath))
        task = conveyor.process.tasksequence(tasks)
        return task

class _DualThingRecipe(_ThingRecipe):
    pass
