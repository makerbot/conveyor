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
import mock
import os
import os.path
import subprocess
import tempfile

import conveyor.address
import conveyor.domain
import conveyor.dualstrusion
import conveyor.enum
import conveyor.log
import conveyor.machine.s3g
import conveyor.process
import conveyor.task
import conveyor.util


class RecipeManager(object):
    def __init__(self, config, server, spool):
        self._config = config
        self._server = server
        self._spool = spool
        self._log = conveyor.log.getlogger(self)

    def get_recipe(self, job):
        root, ext = os.path.splitext(job.input_file)
        if '.gcode' == ext.lower():
            recipe = self._get_recipe_gcode(job)
        elif '.stl' == ext.lower():
            recipe = self._get_recipe_stl(job)
        elif '.thing' == ext.lower():
            recipe = self._get_recipe_thing(job)
        else:
            raise conveyor.error.UnsupportedModelTypeException(job.input_file)
        return recipe

    def _get_recipe_gcode(self, job):
        if not os.path.exists(job.input_file):
            raise conveyor.error.MissingFileException(job.input_file)
        elif not os.path.isfile(job.input_file):
            raise conveyor.error.NotFileException(job.input_file)
        else:
            recipe = _GcodeRecipe(self._server, self._config, job, self._spool, job.input_file)
        return recipe

    def _get_recipe_stl(self, job):
        if not os.path.exists(job.input_file):
            raise conveyor.error.MissingPathException(job.input_file)
        elif not os.path.isfile(job.input_file):
            raise conveyor.error.NotFileException(job.input_file)
        else:
            recipe = _StlRecipe(self._server, self._config, job, self._spool, job.input_file)
            return recipe

    def _get_recipe_thing(self, job):
        if not os.path.exists(job.input_file):
            raise conveyor.error.MissingFileException(job.input_file)
        else:
            thing_dir = tempfile.mkdtemp(suffix='.thing')
            unified_mesh_hack = self._config.get('server', 'unified_mesh_hack_exe')
            popen = subprocess.Popen(
                [unified_mesh_hack, job.input_file, thing_dir],
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
                raise InvalidThingException(job.input_file)
            else:
                self._log.debug('unified_mesh_hack terminated with code %d', code)
                stl_0_path = os.path.join(thing_dir, 'UNIFIED_MESH_HACK_0.stl')
                stl_1_path = os.path.join(thing_dir, 'UNIFIED_MESH_HACK_1.stl')
                if os.path.exists(stl_0_path) and os.path.exists(stl_1_path):
                    recipe = _DualThingRecipe(
                        self._server, self._config, job, self._spool, stl_0_path, stl_1_path)
                    pass
                elif os.path.exists(stl_0_path):
                    recipe = _SingleThingRecipe(
                        self._server, self._config, job, self._spool, stl_0_path)
                elif os.path.exists(stl_1_path):
                    recipe = _SingleThingRecipe(
                        self._server, self._config, job, self._spool, stl_1_path)
                else:
                    raise InvalidThingException(job.input_file)
                return recipe


# TODO: re-order the constructor arguments so they match the rest of the
# system.

class Recipe(object):
    def __init__(self, server, config, job, spool):
        self._config = config
        self._log = conveyor.log.getlogger(self)
        self._job = job
        self._server = server
        self._spool = spool

    def getgcodeprocessors(self, profile):
        gcodeprocessors = self._job.gcode_processor_name
        if None is gcodeprocessors:
            gcodeprocessors = []
        if (conveyor.slicer.Slicer.SKEINFORGE == self._job.slicer_name):
            # custom profile (has own start/end)
            if self._job.slicer_settings.path is None:
                if 'AnchorProcessor' not in gcodeprocessors:
                    gcodeprocessors.insert(0, 'AnchorProcessor')
            if 'Skeinforge50Processor' not in gcodeprocessors:
                gcodeprocessors.append('Skeinforge50Processor')
            if profile.name == 'Replicator2':
                if 'FanProcessor' not in gcodeprocessors:
                    gcodeprocessors.append('FanProcessor')
        return gcodeprocessors

    def _slicertask(self, profile, input_path, output_path, add_start_end,
            dualstrusion, slicer_settings):
        if conveyor.slicer.Slicer.MIRACLEGRUE == self._job.slicer_name:
            exe = self._config.get('miracle_grue', 'exe')
            profile_dir = self._config.get('miracle_grue', 'profile_dir')
            def running_callback(task):
                def work():
                    slicer = conveyor.slicer.miraclegrue.MiracleGrueSlicer(
                        profile, input_path, output_path, add_start_end,
                        slicer_settings, self._job.material_name,
                        dualstrusion, task, exe, profile_dir)
                    slicer.slice()
                self._server.queue_work(work)
        elif conveyor.slicer.Slicer.SKEINFORGE == self._job.slicer_name:
            file_ = self._config.get('skeinforge', 'file')
            profile_dir = self._config.get('skeinforge', 'profile_dir')
            skeinforge_profile = self._config.get('skeinforge', 'profile')
            profile_file = os.path.join(profile_dir, skeinforge_profile)
            def running_callback(task):
                def work():
                    slicer = conveyor.slicer.skeinforge.SkeinforgeSlicer(
                        profile, input_path, output_path, add_start_end,
                        slicer_settings, self._job.material_name,
                        dualstrusion, task, file_, profile_file)
                    slicer.slice()
                self._server.queue_work(work)
        else:
            raise ValueError(self._job.slicer_name)
        task = conveyor.task.Task()
        task.runningevent.attach(running_callback)
        return task

    def _gcodeprocessortask(self, inputpath, outputpath, profile):
        factory = makerbot_driver.GcodeProcessors.ProcessorFactory()
        gcodeprocessor_list = self.getgcodeprocessors(profile._s3g_profile)
        gcodeprocessors = list(factory.get_processors(gcodeprocessor_list, profile._s3g_profile))
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
                weaver = conveyor.dualstrusion.DualstrusionWeaver(t0_codes, t1_codes, task)
                woven_codes = weaver.combine_codes()
                progress_processor = makerbot_driver.GcodeProcessors.DualstrusionProgressProcessor()
                output = progress_processor.process_gcode(woven_codes)
                with open(outputpath, 'w') as f:
                    for line in output:
                        f.write(line)
            except Exception as e:
                self._log.debug("unhandled exception", exc_info=True)
                task.fail(e)
            else:
                task.end(None)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task

    def _postweavetask(self, gcode_path, gcode_path_tmp, gcode_path_out, profile):
        def runningcallback(task):
            self._log.info("postweave processing on %s" % (gcode_path))
            conveyor.dualstrusion.post_weave(gcode_path, gcode_path_tmp, gcode_path_out, profile)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task

    def _printtask(self, machine, inputpath, dualstrusion):
        def runningcallback(task):
            self._spool.spool_print(
                machine, inputpath, True,
                self._job.extruder_name,
                self._job.slicer_settings.extruder_temperature,
                self._job.slicer_settings.platform_temperature,
                self._job.material_name, self._job.name, task,)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task

    def _print_to_filetask(self, input_file, output_file):
        def runningcallback(task):
            def work():
                self._job.driver.print_to_file(
                    self._job.profile, input_file, output_file,
                    self._job.file_type, True, self._job.extruder_name,
                    self._job.slicer_settings.extruder_temperature,
                    self._job.slicer_settings.platform_temperature,
                    self._job.material_name, self._job.name, task)
            self._server.queue_work(work)
        task = conveyor.task.Task()
        task.runningevent.attach(runningcallback)
        return task

    @staticmethod
    def verifys3gtask(s3gpath):
        """
        This function is static so it can be accessed by server/__init__.py when 
        executing the verifys3g command.
        """
        task = conveyor.task.Task()

        def update(percent):
            percent = min(percent, 100)
            progress = {
                'name': 'verify',
                'progress': percent
            }
            # Use regular heartbeat here, since we cant keep track of past updates
            if progress != task.progress:
                task.heartbeat(progress)

        def runningcallback(task):
            # If the filereader can parse it, then the s3g file is valid
            reader = makerbot_driver.FileReader.FileReader()
            try:
                with open(s3gpath, 'rb') as reader.file:
                    payloads = reader.ReadFile(update)
                task.end(True)
            except makerbot_driver.FileReader.S3gStreamError as e:
                message = unicode(e)
                task.fail(message)
        task.runningevent.attach(runningcallback)
        return task

    def verifygcodetask(self, gcodepath, profile, slicer_settings, material_name, dualstrusion):
        task = conveyor.task.Task()
        def update(percent):
            percent = min(percent, 100) 
            progress = {
                'name': 'verify',
                'progress': percent,
            }
            # Use regular heartbeat here, since we cant keep track of past updates
            if progress != task.progress:
                task.heartbeat(progress)
        def runningcallback(task):
            self._log.info("Validating gcode file %s" % (gcodepath))
            parser = makerbot_driver.Gcode.GcodeParser()
            parser.state.values['build_name'] = "VALIDATION"
            parser.state.profile = profile._s3g_profile
            parser.s3g = mock.Mock()
            extruders = [e.strip() for e in slicer_settings.extruder.split(',')]
            gcode_scaffold = profile.get_gcode_scaffold(
                extruders,
                slicer_settings.extruder_temperature,
                slicer_settings.platform_temperature,
                material_name)
            parser.environment.update(gcode_scaffold.variables)
            try:
                with open(gcodepath) as f:
                    for line in f:
                        parser.execute_line(line)
                        update(parser.state.percentage)
            except makerbot_driver.Gcode.GcodeError as e:
                self._log.exception('G-code error')
                message = conveyor.util.exception_to_failure(e)
                task.fail(message)
            else:
                task.end(True)
        task.runningevent.attach(runningcallback)
        return task

    def _add_start_end_task(self, profile, slicer_settings, material_name,
            add_start_end, dualstrusion, input_path, output_path):
        def running_callback(task):
            self._log.info("Writing out gcode to %s with%s start/end gcode" % (output_path, '' if add_start_end else 'out'))
            try:
                with open(input_path) as ifp:
                    with open(output_path, 'w') as ofp:
                        extruders = [e.strip() for e in slicer_settings.extruder.split(',')]
                        gcode_scaffold = profile.get_gcode_scaffold(
                            extruders,
                            slicer_settings.extruder_temperature,
                            slicer_settings.platform_temperature,
                            material_name)
                        if add_start_end:
                            for line in gcode_scaffold.start:
                                print(line, file=ofp)
                        for line in ifp.readlines():
                            ofp.write(line)
                        if add_start_end:
                            for line in gcode_scaffold.end:
                                print(line, file=ofp)
            except Exception as e:
                self._log.debug("unhandled exception", exc_info=True)
                task.fail(e)
            else:
                task.end(None)
        task = conveyor.task.Task()
        task.runningevent.attach(running_callback)
        return task

    def print(self):
        raise NotImplementedError

    def print_to_file(self):
        raise NotImplementedError

    def slice(self):
        raise NotImplementedError


class _GcodeRecipe(Recipe):
    def __init__(self, server, config, job, spool, gcodepath):
        Recipe.__init__(self, server, config, job, spool)
        self._gcodepath = gcodepath

    def print(self):
        dualstrusion = False
        tasks = []

        with tempfile.NamedTemporaryFile(suffix='.gcode') as outputfp:
            outputpath = outputfp.name
        profile = self._job.machine.get_profile()
        add_start_end = not self._job.has_start_end
        add_start_end_task = self._add_start_end_task(
            profile, self._job.slicer_settings, self._job.material_name,
            add_start_end, dualstrusion, self._job.input_file, outputpath)
        tasks.append(add_start_end_task)

        #verify
        profile = self._job.machine.get_profile()
        verifytask = self.verifygcodetask(outputpath, profile, self._job.slicer_settings, self._job.material_name, dualstrusion)
        tasks.append(verifytask)

        # Print
        printtask = self._printtask(self._job.machine, outputpath, False)
        tasks.append(printtask)

        process = conveyor.process.tasksequence(self._job, tasks)
        return process


    def print_to_file(self):
        tasks = []
        dualstrusion = False

        with tempfile.NamedTemporaryFile(suffix='.gcode') as start_end_pathfp:
            start_end_path = start_end_pathfp.name
        add_start_end = not self._job.has_start_end
        add_start_end_task = self._add_start_end_task(
            self._job.profile, self._job.slicer_settings, self._job.material_name,
            add_start_end, dualstrusion, self._job.input_file, start_end_path)
        tasks.append(add_start_end_task)

        #verify
        verifytask = self.verifygcodetask(start_end_path, self._job.profile, self._job.slicer_settings, self._job.material_name, dualstrusion)
        tasks.append(verifytask)

        # Print
        print_to_filetask = self._print_to_filetask(start_end_path, self._job.output_file)
        tasks.append(print_to_filetask)

        tasks.append(self.verifys3gtask(self._job.output_file))

        def process_endcallback(task):
            os.unlink(start_end_path)
        process = conveyor.process.tasksequence(self._job, tasks)
        process.endevent.attach(process_endcallback)
        return process


class _StlRecipe(Recipe):
    def __init__(self, server, config, job, spool, stlpath):
        Recipe.__init__(self, server, config, job, spool)
        self._stlpath = stlpath

    def print(self):
        dualstrusion = False
        tasks = []

        # Slice
        with tempfile.NamedTemporaryFile(suffix='.gcode') as gcodefp:
            gcodepath = gcodefp.name
        profile = self._job.machine.get_profile()
        slicetask = self._slicertask(
            profile, self._stlpath, gcodepath, False, False,
            self._job.slicer_settings)
        tasks.append(slicetask)

        # Process Gcode
        gcodeprocessors = self.getgcodeprocessors(profile._s3g_profile)
        if 0 == len(gcodeprocessors):
            processed_gcodepath = gcodepath
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as processed_gcodefp:
                processed_gcodepath = processed_gcodefp.name
            gcodeprocessortask = self._gcodeprocessortask(
                gcodepath, processed_gcodepath, profile)
            tasks.append(gcodeprocessortask)

        with tempfile.NamedTemporaryFile(suffix='.gcode') as outputfp:
            outputpath = outputfp.name
        add_start_end = not self._job.has_start_end
        add_start_end_task = self._add_start_end_task(
            profile, self._job.slicer_settings, self._job.material_name,
            add_start_end, dualstrusion, processed_gcodepath, outputpath)
        tasks.append(add_start_end_task)

        #verify
        verifytask = self.verifygcodetask(outputpath, profile, self._job.slicer_settings, self._job.material_name, dualstrusion)
        tasks.append(verifytask)

        # Print
        printtask = self._printtask(self._job.machine, outputpath, False)
        tasks.append(printtask)

        def process_endcallback(task):
            os.unlink(gcodepath)
            if gcodepath != processed_gcodepath:
                os.unlink(processed_gcodepath)
        process = conveyor.process.tasksequence(self._job, tasks)
        process.endevent.attach(process_endcallback)
        return process

    def print_to_file(self):
        tasks = []
        dualstrusion = False

        # Slice
        with tempfile.NamedTemporaryFile(suffix='.gcode') as gcodefp:
            gcodepath = gcodefp.name
        slicetask = self._slicertask(
            self._job.profile, self._stlpath, gcodepath, False, False,
            self._job.slicer_settings)
        tasks.append(slicetask)

        # Process Gcode
        gcodeprocessors = self.getgcodeprocessors(self._job.profile._s3g_profile)
        if 0 == len(gcodeprocessors):
            processed_gcodepath = gcodepath
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as processed_gcodefp:
                processed_gcodepath = processed_gcodefp.name
            gcodeprocessortask = self._gcodeprocessortask(
                gcodepath, processed_gcodepath, self._job.profile)
            tasks.append(gcodeprocessortask)

        with tempfile.NamedTemporaryFile(suffix='.gcode') as start_end_pathfp:
            start_end_path = start_end_pathfp.name
        add_start_end = not self._job.has_start_end
        add_start_end_task = self._add_start_end_task(
            self._job.profile, self._job.slicer_settings, self._job.material_name,
            add_start_end, dualstrusion, processed_gcodepath, start_end_path)
        tasks.append(add_start_end_task)

        #verify
        verifytask = self.verifygcodetask(start_end_path, self._job.profile, self._job.slicer_settings, self._job.material_name, dualstrusion)
        tasks.append(verifytask)

        # Print
        print_to_filetask = self._print_to_filetask(start_end_path, self._job.output_file)
        tasks.append(print_to_filetask)

        tasks.append(self.verifys3gtask(self._job.output_file))

        def process_endcallback(task):
            os.unlink(gcodepath)
            if gcodepath != processed_gcodepath:
                os.unlink(processed_gcodepath)
        process = conveyor.process.tasksequence(self._job, tasks)
        process.endevent.attach(process_endcallback)
        return process

    def slice(self):
        tasks = []

        # Slice
        with tempfile.NamedTemporaryFile(suffix='.gcode') as gcodefh:
            gcodepath = gcodefh.name
        slicetask = self._slicertask(
            self._job.profile, self._stlpath, gcodepath, False, False,
            self._job.slicer_settings)
        tasks.append(slicetask)

        gcodeprocessors = self.getgcodeprocessors(self._job.profile._s3g_profile)
        if 0 == len(gcodeprocessors):
            processed_gcodepath = gcodepath 
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as processed_gcodefp:
                processed_gcodepath = processed_gcodefp.name

        # Process Gcode
        if 0 != len(gcodeprocessors):
            gcodeprocessortask = self._gcodeprocessortask(gcodepath, processed_gcodepath, self._job.profile)
            tasks.append(gcodeprocessortask)

        add_start_end_task = self._add_start_end_task(
            self._job.profile, self._job.slicer_settings, self._job.material_name,
            self._job.add_start_end, False, processed_gcodepath,
            self._job.output_file)
        tasks.append(add_start_end_task)

        def process_endcallback(task):
            if gcodepath != self._job.output_file:
                os.unlink(gcodepath)

        process = conveyor.process.tasksequence(self._job, tasks)
        process.endevent.attach(process_endcallback)
        return process


class _ThingRecipe(Recipe):
    pass


class _SingleThingRecipe(_ThingRecipe):
    def __init__(self, server, config, job, spool, stl_path):
        _ThingRecipe.__init__(self, server, config, job, spool)
        self._stl_path = stl_path

    def print(self):
        stlrecipe = _StlRecipe(
            self._server, self._config, self._job, self._spool, self._stl_path)
        process = stlrecipe.print()
        return process

    def print_to_file(self):
        stlrecipe = _StlRecipe(
            self._server, self._config, self._job, self._spool, self._stl_path)
        process = stlrecipe.print_to_file()
        return process

    def slice(self):
        stlrecipe = _StlRecipe(
            self._server, self._config, self._job, self._spool, self._stl_path)
        process = stlrecipe.slice()
        return process


class _DualThingRecipe(_ThingRecipe):
    def __init__(self, server, config, job, spool, stl_0_path, stl_1_path):
        _ThingRecipe.__init__(self, server, config, job, spool)
        self._stl_0_path = stl_0_path
        self._stl_1_path = stl_1_path

    def print_to_file(self):
        tasks = []
        dualstrusion = True
        stl_1_path = self._stl_1_path
        with tempfile.NamedTemporaryFile(suffix='.0.gcode') as f:
            gcode_0_path = f.name
        with tempfile.NamedTemporaryFile(suffix='.1.gcode') as f:
            gcode_1_path = f.name

        add_start_end = False

        settings_0 = conveyor.domain.SlicerConfiguration.fromdict(self._job.slicer_settings.todict())
        settings_0.extruder = '0'
        slice_0_task = self._slicertask(
            self._job.profile, self._stl_0_path, gcode_0_path, False, True, settings_0)
        tasks.append(slice_0_task)

        settings_1 = conveyor.domain.SlicerConfiguration.fromdict(self._job.slicer_settings.todict())
        settings_1.extruder = '1'
        slice_1_task = self._slicertask(
            self._job.profile, self._stl_1_path, gcode_1_path, False, True, settings_1)
        tasks.append(slice_1_task)

        #Combine for dualstrusion
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=True) as f:
            dualstrusion_path = f.name
        tasks.append(self._dualstrusiontask(gcode_0_path, gcode_1_path, dualstrusion_path))

        # Process Gcode
        gcodeprocessors = self.getgcodeprocessors(self._job.profile._s3g_profile)
        if 0 == len(gcodeprocessors):
            processed_gcodepath = dualstrusion_path
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as processed_gcodefp:
                processed_gcodepath = processed_gcodefp.name
            gcodeprocessortask = self._gcodeprocessortask(
                dualstrusion_path, processed_gcodepath, self._job.profile)
            tasks.append(gcodeprocessortask)

        #Process gcode post-weave and grooming
        with tempfile.NamedTemporaryFile(suffix='.dual.tmp.gcode') as f:
            tmp_dual_path = f.name
        with tempfile.NamedTemporaryFile(suffix='.dual.fix.gcode') as f:
            fixed_dual_path = f.name
        tasks.append(self._postweavetask(processed_gcodepath, tmp_dual_path, fixed_dual_path, self._job.profile))


        with tempfile.NamedTemporaryFile(suffix='.gcode') as start_end_pathfp:
            start_end_path = start_end_pathfp.name
        add_start_end = True
        add_start_end_task = self._add_start_end_task(
            self._job.profile, self._job.slicer_settings, self._job.material_name,
            add_start_end, dualstrusion, fixed_dual_path, start_end_path)
        tasks.append(add_start_end_task)

        #verify
        verifytask = self.verifygcodetask(start_end_path, self._job.profile, self._job.slicer_settings, self._job.material_name, dualstrusion)
        tasks.append(verifytask)

        # Print To File
        print_to_filetask = self._print_to_filetask(start_end_path, self._job.output_file)
        tasks.append(print_to_filetask)

        tasks.append(self.verifys3gtask(self._job.output_file))

        process = conveyor.process.tasksequence(self._job, tasks)
        def process_endcallback(task):
            for path in [gcode_0_path, gcode_1_path, processed_gcodepath, tmp_dual_path, fixed_dual_path]:
                os.unlink(path)
        process.endevent.attach(process_endcallback)
        return process

    def slice(self):
        tasks = []
        with tempfile.NamedTemporaryFile(suffix='.0.gcode') as f:
            gcode_0_path = f.name
        with tempfile.NamedTemporaryFile(suffix='.1.gcode') as f:
            gcode_1_path = f.name

        add_start_end = False

        settings_0 = conveyor.domain.SlicerConfiguration.fromdict(self._job.slicer_settings.todict())
        settings_0.extruder = '0'
        slice_0_task = self._slicertask(
            self._job.profile, self._stl_0_path, gcode_0_path, False, True,
            settings_0)
        tasks.append(slice_0_task)

        settings_1 = conveyor.domain.SlicerConfiguration.fromdict(self._job.slicer_settings.todict())
        settings_1.extruder = '1'
        slice_1_task = self._slicertask(
            self._job.profile, self._stl_1_path, gcode_1_path, False, True,
            settings_1)
        tasks.append(slice_1_task)

        #Combine for dualstrusion
        with tempfile.NamedTemporaryFile(suffix='.gcode') as f:
            dualstrusion_path = f.name
        tasks.append(self._dualstrusiontask(gcode_0_path, gcode_1_path, dualstrusion_path))

        # Process Gcode
        with tempfile.NamedTemporaryFile(suffix='.dual.gcode') as f:
            dual_path = f.name
        gcodeprocessors = self.getgcodeprocessors(self._job.profile._s3g_profile)
        gcodeprocessortask = self._gcodeprocessortask(
            dualstrusion_path, dual_path, self._job.profile)
        tasks.append(gcodeprocessortask)

        #Process gcode post-weave and grooming
        with tempfile.NamedTemporaryFile(suffix='.dual.tmp.gcode') as f:
            tmp_dual_path = f.name
        with tempfile.NamedTemporaryFile(suffix='.dual.fix.gcode') as f:
            fixed_dual_path = f.name
        tasks.append(self._postweavetask(dual_path, tmp_dual_path, fixed_dual_path, self._job.profile))

        add_start_end_task = self._add_start_end_task(
            self._job.profile, self._job.slicer_settings, self._job.material_name,
            self._job.add_start_end, True, fixed_dual_path, self._job.output_file)
        tasks.append(add_start_end_task)

        process = conveyor.process.tasksequence(self._job, tasks)
        def process_endcallback(task):
            for path in [gcode_0_path, gcode_1_path, dualstrusion_path, dual_path, tmp_dual_path, fixed_dual_path]:
                os.unlink(path)
        process.endevent.attach(process_endcallback)
        return process

    def print(self):
        dualstrusion = True
        profile = self._job.machine.get_profile()
        tasks = []
        with tempfile.NamedTemporaryFile(suffix='.0.gcode') as f:
            gcode_0_path = f.name
        with tempfile.NamedTemporaryFile(suffix='.1.gcode') as f:
            gcode_1_path = f.name

        add_start_end = False

        settings_0 = conveyor.domain.SlicerConfiguration.fromdict(self._job.slicer_settings.todict())
        settings_0.extruder = '0'
        slice_0_task = self._slicertask(
            profile, self._stl_0_path, gcode_0_path, False, True,
            settings_0)
        tasks.append(slice_0_task)

        settings_1 = conveyor.domain.SlicerConfiguration.fromdict(self._job.slicer_settings.todict())
        settings_1.extruder = '1'
        slice_1_task = self._slicertask(
            profile, self._stl_1_path, gcode_1_path, False, True,
            settings_1)
        tasks.append(slice_1_task)

        #Combine for dualstrusion
        with tempfile.NamedTemporaryFile(suffix='.gcode') as f:
            dualstrusion_path = f.name
        tasks.append(self._dualstrusiontask(gcode_0_path, gcode_1_path, dualstrusion_path))

        # Process Gcode
        gcodeprocessors = self.getgcodeprocessors(profile._s3g_profile)
        if 0 == len(gcodeprocessors):
            processed_gcodepath = dualstrusion_path
        else:
            with tempfile.NamedTemporaryFile(suffix='.gcode') as processed_gcodefp:
                processed_gcodepath = processed_gcodefp.name
            gcodeprocessortask = self._gcodeprocessortask(
                dualstrusion_path, processed_gcodepath, profile)
            tasks.append(gcodeprocessortask)

        #Process gcode post-weave and grooming
        with tempfile.NamedTemporaryFile(suffix='.dual.tmp.gcode') as f:
            tmp_dual_path = f.name
        with tempfile.NamedTemporaryFile(suffix='.dual.fix.gcode') as f:
            fixed_dual_path = f.name
        tasks.append(self._postweavetask(processed_gcodepath, tmp_dual_path, fixed_dual_path, self._job.profile))

        with tempfile.NamedTemporaryFile(suffix='.gcode') as outputpathfp:
            outputpath = outputpathfp.name
        add_start_end = True
        add_start_end_task = self._add_start_end_task(
            profile, self._job.slicer_settings, self._job.material_name,
            add_start_end, dualstrusion, fixed_dual_path, outputpath)
        tasks.append(add_start_end_task)

        #verify
        profile = self._job.machine.get_profile()
        verifytask = self.verifygcodetask(outputpath, profile, self._job.slicer_settings, self._job.material_name, dualstrusion)
        tasks.append(verifytask)

        #print
        printtask = self._printtask(self._job.machine, outputpath, True)
        tasks.append(printtask)

        process = conveyor.process.tasksequence(self._job, tasks)
        def process_endcallback(task):
            for path in [gcode_0_path, gcode_1_path, dualstrusion_path, processed_gcodepath, tmp_dual_path, fixed_dual_path]:
                os.unlink(path)
        process.endevent.attach(process_endcallback)
        return process


class InvalidThingException(Exception):
    def __init__(self, path):
        Exception.__init__(self, path)
        self.path = path
