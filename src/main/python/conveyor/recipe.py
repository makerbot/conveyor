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
import shutil
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

    def cook(self, job):
        recipe = self._lookup(job)
        tasks = list(_flatten(recipe.get_tasks()))
        conveyor.process.tasksequence(job, tasks)

    def _lookup(self, job):
        recipe = _UnifiedRecipe(
            self._config, self._server, self._spool, job)
        return recipe


def _flatten(obj):
    if isinstance(obj, conveyor.task.Task):
        yield obj
    else:
        for obj2 in obj:
            for obj3 in _flatten(obj2):
                yield obj3


class _Recipe(object):
    def __init__(self, config, server, spool, job):
        self._config = config
        self._server = server
        self._spool = spool
        self._job = job
        self._log = conveyor.log.getlogger(self)

    def get_tasks(self):
        raise NotImplementedError


def _task(func):
    def decorator(self, *args, **kwargs):
        def running_callback(task):
            try:
                func(self, task, *args, **kwargs)
            except Exception as e:
                self._log.exception('unhandled exception; task failed')
                if conveyor.task.TaskState.RUNNING == task.state:
                    failure = conveyor.util.exception_to_failure(e)
                    task.fail(failure)
        task = conveyor.task.Task()
        task.runningevent.attach(running_callback)
        return task
    return decorator


def _work(func):
    def decorator(self, task, *args, **kwargs):
        def work():
            try:
                func(self, task, *args, **kwargs)
                if conveyor.task.TaskState.RUNNING == task.state:
                    self._log.warning('task not ended')
                    task.end(None)
            except Exception as e:
                self._log.exception('unhandled exception; task failed')
                if conveyor.task.TaskState.RUNNING == task.state:
                    failure = conveyor.util.exception_to_failure(e)
                    task.fail(failure)
        self._server.queue_work(work)
    return decorator


class _UnifiedRecipe(_Recipe):
    def __init__(self, config, server, spool, job):
        _Recipe.__init__(self, config, server, spool, job)
        self._job_dir = None

    def get_tasks(self):
        prefix = ''.join(('conveyor.', str(self._job.id), '.'))
        self._job_dir = tempfile.mkdtemp(prefix=prefix)
        input_ = _Variable(None, None, self._job.input_file)
        return self._goto_input_file(input_)

    # There are several kinds of g-code used by this recipe:
    #
    #   layer-gcode     - layer g-code without any start/end g-code
    #   processed-gcode - the layer-gcode after gcode processors are run
    #                     without any start/end g-code
    #   whole-gcode     - the processed-gcode along with start/end g-code

    # See conveyor/doc/recipe.{png,svg}.
    #
    # The diagram's merge nodes correspond to the `_goto` methods (these are
    # actually proper function calls, not unrestricted `goto`). These methods
    # are generally named after the value which was just produced (e.g.,
    # `_goto_layer_gcode` meaning the `layer_gcode` was produced and the recipe
    # should do something interesting with it). The `_goto` methods must be
    # called in a tail position.
    #
    # The control flow arcs correspond to variables. We use first-class
    # variables here so we can pass them around and bind them into functions
    # (a.k.a, merge nodes) before they have values. In the current
    # implementation all variables represent files. The methods `_temp_file`
    # and `_temp_file_name` create real files in the `_job_dir` and set the
    # variable's value to the file name.
    #
    # The decision nodes and their predicates correspond to the `if` statements
    # in the code. The branches often have the side effect of assigning a value
    # to a variable or copying a value from one variable to another.
    #
    # Be aware that the variable-related parameters of tasks are often written
    # in assignment form, i.e., the destination is the first parameter and the
    # source is the second. In other words, the first parameter is often the
    # return value.
    #
    # Anyway, it all starts when you have an `input_file`...

    def _goto_input_file(self, input_):
        input_file = input_.get()
        root, ext = os.path.splitext(input_file)
        ext = ext.lower()
        if '.gcode' == ext:
            if not self._job.get_has_start_end():
                dualstrusion = False
                yield self._goto_layer_gcode(input_, dualstrusion)
            else:
                yield self._goto_whole_gcode(input_)
        elif '.stl' == ext:
            yield self._goto_stl(input_)
        elif '.thing' == ext:
            yield self._goto_thing(input_)
        else:
            raise conveyor.error.UnsupportedModelTypeException(input_file)

    def _goto_stl(self, stl):
        layer_gcode = self._layer_gcode_var()
        dualstrusion = False
        yield self._slice_task(
            layer_gcode, stl, self._job.slicer_settings, dualstrusion)
        yield self._goto_layer_gcode(layer_gcode, dualstrusion)

    def _goto_thing(self, thing):
        thing_file = thing.get()
        if not os.path.exists(thing_file):
            raise conveyor.error.MissingFileException(thing_file)
        else:
            thing_dir = tempfile.mkdtemp(
                prefix='thing-dir', dir=self._job_dir)
            unified_mesh_hack = self._config.get(
                'server', 'unified_mesh_hack_exe')
            popen = subprocess.Popen(
                [unified_mesh_hack, thing_file, thing_dir],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            while True:
                line = popen.stdout.readline()
                if '' == line:
                    break
                else:
                    self._log.info('%s', line)
            code = popen.wait()
            if 0 != code:
                self._log.error(
                    'failed to extract meshes; unified_mesh_hack terminated with code %d',
                    code)
                raise InvalidThingException(thing_file)
            else:
                self._log.debug(
                    'unified_mesh_hack terminated with code %d', code)
                stl_0_file = os.path.join(
                    thing_dir, 'UNIFIED_MESH_HACK_0.stl')
                stl_1_file = os.path.join(
                    thing_dir, 'UNIFIED_MESH_HACK_1.stl')
                if (os.path.exists(stl_0_file)
                        and os.path.exists(stl_1_file)):
                    layer_gcode = self._layer_gcode_var()
                    layer_gcode_0 = self._layer_gcode_var(suffix='0')
                    layer_gcode_1 = self._layer_gcode_var(suffix='1')
                    stl_0 = self._stl_var(stl_0_file, '0')
                    stl_1 = self._stl_var(stl_1_file, '1')
                    settings_0 = self._override_extruder('0')
                    settings_1 = self._override_extruder('1')
                    dualstrusion = True
                    yield self._slice_task(
                        layer_gcode_0, stl_0, settings_0, dualstrusion)
                    yield self._slice_task(
                        layer_gcode_1, stl_1, settings_1, dualstrusion)
                    yield self._weave_task(
                        layer_gcode, layer_gcode_0, layer_gcode_1)
                    yield self._goto_layer_gcode(layer_gcode, dualstrusion)
                elif os.path.exists(stl_0_file):
                    stl = self._stl_var(stl_0_file)
                    yield self._goto_stl(stl)
                elif os.path.exists(stl_1_file):
                    stl = self._stl_var(stl_1_file)
                    yield self._goto_stl(stl)
                else:
                    raise InvalidThingException(thing_file)

    def _override_extruder(self, extruder):
        new_settings = conveyor.domain.SlicerConfiguration.fromdict(
            self._job.slicer_settings.to_dict())
        new_settings.extruder = extruder
        return new_settings

    def _goto_layer_gcode(self, layer_gcode, dualstrusion):
        processed_gcode = _Variable('processed-gcode', 'gcode')
        yield self._gcode_processor_task(
            processed_gcode, layer_gcode, dualstrusion)
        if not self._job.get_add_start_end():
            yield self._goto_output_file(processed_gcode)
        else:
            whole_gcode = _Variable('whole-gcode', 'gcode')
            yield self._add_start_end_task(whole_gcode, processed_gcode)
            yield self._goto_whole_gcode(whole_gcode)

    def _goto_whole_gcode(self, whole_gcode):
        if isinstance(self._job, conveyor.job.PrintJob):
            yield self._verify_gcode_task(whole_gcode)
            yield self._print_task(whole_gcode)
            yield self._goto_end()
        elif isinstance(self._job, conveyor.job.PrintToFileJob):
            s3g = _Variable('s3g', self._job.file_type)
            yield self._print_to_file_task(s3g, whole_gcode)
            yield self._verify_s3g_task(s3g)
            yield self._goto_output_file(s3g)
        elif isinstance(self._job, conveyor.job.SliceJob):
            yield self._verify_gcode_task(whole_gcode)
            yield self._goto_output_file(whole_gcode)
        else:
            raise ValueError(self._job)

    def _goto_output_file(self, output):
        yield self._copy_output_file_task(output)
        yield self._goto_end()

    def _goto_end(self):
        return ()

    #
    # Variables
    #

    def _stl_var(self, value=None, suffix=None):
        prefix = 'stl'
        if None is not suffix:
            prefix = ''.join((prefix, '-', suffix))
        stl = _Variable(prefix, 'stl', value)
        return stl

    def _layer_gcode_var(self, value=None, suffix=None):
        prefix = 'layer-gcode'
        if None is not suffix:
            prefix = ''.join((prefix, '-', suffix))
        layer_gcode = _Variable(prefix, 'gcode', value)
        return layer_gcode

    def _temp_file(self, variable):
        if None is variable.prefix:
            prefix = ''
        else:
            prefix = ''.join((variable.prefix, '.'))
        if None is variable.suffix:
            suffix = ''
        else:
            suffix = ''.join(('.', variable.suffix))
        fp = tempfile.NamedTemporaryFile(
            mode='w+', suffix=suffix, prefix=prefix, dir=self._job_dir,
            delete=False)
        variable.set(fp.name)
        return fp

    def _temp_file_name(self, variable):
        fp = self._temp_file(variable)
        fp.close()
        name = variable.get()
        return name

    #
    # Tasks
    #

    @_task
    @_work
    def _slice_task(
            self, task, layer_gcode, stl, slicer_settings, dualstrusion):
        profile = self._job.get_profile()
        input_file = stl.get()
        output_file = self._temp_file_name(layer_gcode)
        self._log.info(
            'job %d: slicing: %s -> %s', self._job.id, input_file,
            output_file)
        if conveyor.slicer.Slicer.MIRACLEGRUE == self._job.slicer_name:
            method = self._get_slicer_miraclegrue
        elif conveyor.slicer.Slicer.SKEINFORGE == self._job.slicer_name:
            method = self._get_slicer_skeinforge
        else:
            raise ValueError(self._job.slicer_name)
        slicer = method(
            profile, input_file, output_file, slicer_settings, dualstrusion,
            task)
        slicer.slice()

    def _get_slicer_miraclegrue(
            self, profile, input_file, output_file, slicer_settings,
            dualstrusion, task):
        exe = self._config.get('miracle_grue', 'exe')
        profile_dir = self._config.get('miracle_grue', 'profile_dir')
        slicer = conveyor.slicer.miraclegrue.MiracleGrueSlicer(
            profile, input_file, output_file, slicer_settings,
            self._job.material_name, dualstrusion, task, exe, profile_dir)
        return slicer

    def _get_slicer_skeinforge(
            self, profile, input_file, output_file, slicer_settings,
            dualstrusion, task):
        file_ = self._config.get('skeinforge', 'file')
        profile_dir = self._config.get('skeinforge', 'profile_dir')
        skeinforge_profile = self._config.get('skeinforge', 'profile')
        profile_file = os.path.join(profile_dir, skeinforge_profile)
        slicer = conveyor.slicer.skeinforge.SkeinforgeSlicer(
            profile, input_file, output_file, slicer_settings,
            self._job.material_name, dualstrusion, task, file_, profile_file)
        return slicer

    @_task
    @_work
    def _weave_task(self, task, layer_gcode, layer_gcode_0, layer_gcode_1):
        layer_gcode_0_file = layer_gcode_0.get()
        layer_gcode_1_file = layer_gcode_1.get()
        with self._temp_file(layer_gcode) as layer_gcode_fp:
            self._log.info(
                'job %d: weaving: %s + %s -> %s',
                layer_gcode_0_file, layer_gcode_1_file, layer_gcode_fp.name)
            with open(layer_gcode_0_file) as layer_gcode_0_fp:
                layer_gcode_0_gcode = conveyor.dualstrusion.GcodeObject(
                    layer_gcode_0_fp)
            with open(layer_gcode_1_file) as layer_gcode_1_fp:
                layer_gcode_1_gcode = conveyor.dualstrusion.GcodeObject(
                    layer_gcode_1_fp)
            weaver = conveyor.dualstrusion.DualstrusionWeaver(
                layer_gcode_0_gcode, layer_gcode_1_gcode, task)
            woven_codes = weaver.combine_codes()
            progress_processor = makerbot_driver.GcodeProcessors.DualstrusionProgressProcessor()
            output = progress_processor.process_gcode(woven_codes)
            for line in output:
                layer_gcode_fp.write(line)
        task.end(None)

    @_task
    @_work
    def _gcode_processor_task(
            self, task, processed_gcode, layer_gcode, dualstrusion):
        profile = self._job.get_profile()
        factory = makerbot_driver.GcodeProcessors.ProcessorFactory()
        gcode_processor_names = list(self._get_gcode_processor_names(
            dualstrusion))
        gcode_processor_list = list(factory.get_processors(
            gcode_processor_names, profile._s3g_profile))
        input_file = layer_gcode.get()
        if 0 == len(gcode_processor_list):
            self._log.info(
                'job %d: processing g-code: no processors selected: %s',
                self._job.id, input_file)
            processed_gcode.set(input_file)
        else:
            with self._temp_file(processed_gcode) as processed_gcode_fp:
                self._log.info(
                    'job %d: processing g-code: %s to %s [%s]', self._job.id,
                    input_file, processed_gcode_fp.name,
                    ', '.join(gcode_processor_names))
                with open(input_file) as input_fp:
                    output = input_fp.readlines()
                for gcode_processor in gcode_processor_list:
                    output = gcode_processor.process_gcode(output)
                for line in output:
                    processed_gcode_fp.write(line)
        task.end(None)

    def _get_gcode_processor_names(self, dualstrusion):
        self._log.info('gcode_processor_names = %r', self._job.gcode_processor_names)
        if None is not self._job.gcode_processor_names:
            gcode_processor_names = self._job.gcode_processor_names
        else:
            gcode_processor_names = self._get_default_gcode_processor_names(
                dualstrusion)
        return gcode_processor_names

    def _get_default_gcode_processor_names(self, dualstrusion):
        profile = self._job.get_profile()
        if conveyor.slicer.Slicer.SKEINFORGE == self._job.slicer_name:
            yield 'AnchorProcessor'
            yield 'Skeinforge50Processor'
        if 'Replicator2' == profile.name:
            yield 'FanProcessor'
        elif 'Replicator2X' == profile.name:
            if not dualstrusion:
                yield 'Rep2XSinglePrimeProcessor'
            else:
                yield 'Rep2XDualstrusionPrimeProcessor'
                yield 'EmptyLayerProcessor'
                yield 'DualRetractProcessor'

    @_task
    @_work
    def _add_start_end_task(self, task, whole_gcode, processed_gcode):
        processed_gcode_file = processed_gcode.get()
        with open(processed_gcode_file) as processed_gcode_fp:
            with self._temp_file(whole_gcode) as whole_gcode_fp:
                self._log.info(
                    'job %d: adding start/end g-code: %s -> %s', self._job.id,
                    processed_gcode_file, whole_gcode_fp.name)
                gcode_scaffold = self._get_gcode_scaffold()
                # NOTE: we use `print` because the start/end g-code needs line
                # endings (they are stored in an JSON array of strings) and
                # `write` because the layer g-code has line endings (because it
                # is stored as a file).
                for line in gcode_scaffold.start:
                    print(line, file=whole_gcode_fp)
                for line in processed_gcode_fp:
                    whole_gcode_fp.write(line)
                for line in gcode_scaffold.end:
                    print(line, file=whole_gcode_fp)
        task.end(None)

    def _get_gcode_scaffold(self):
        if None is self._job.slicer_settings.path:
            extruders = [
                e.strip() for e in self._job.slicer_settings.extruder.split(',')]
            profile = self._job.get_profile()
            gcode_scaffold = profile.get_gcode_scaffold(
                extruders,
                self._job.slicer_settings.extruder_temperature,
                self._job.slicer_settings.platform_temperature,
                self._job.material_name)
        else:
            if conveyor.slicer.Slicer.MIRACLEGRUE == self._job.slicer_name:
                slicer = conveyor.slicer.miraclegrue.MiracleGrueSlicer
            elif conveyor.slicer.Slicer.SKEINFORGE == self._job.slicer_name:
                slicer = conveyor.slicer.skeinforge.SkeinforgeGrueSlicer
            else:
                raise ValueError(self._job.slicer_name)
            gcode_scaffold = slicer.get_gcode_scaffold(
                self._job.slicer_settings.path)
        return gcode_scaffold


    @_task
    @_work
    def _print_to_file_task(self, task, s3g, whole_gcode):
        profile = self._job.get_profile()
        input_file = whole_gcode.get()
        output_file = self._temp_file_name(s3g)
        self._log.info(
            'job %d: printing to file: %s -> %s', self._job.id, input_file,
            output_file)
        has_start_end = True
        self._job.driver.print_to_file(
            profile, input_file, output_file, self._job.file_type,
            self._job.extruder_name,
            self._job.slicer_settings.extruder_temperature,
            self._job.slicer_settings.platform_temperature,
            self._job.material_name, self._job.name, task)

    @_task
    @_work
    def _verify_gcode_task(self, task, whole_gcode):
        profile = self._job.get_profile()
        parser = makerbot_driver.Gcode.GcodeParser()
        parser.state.values['build_name'] = self._job.name
        parser.state.profile = profile._s3g_profile
        parser.s3g = mock.Mock()
        gcode_scaffold = self._get_gcode_scaffold()
        parser.environment.update(gcode_scaffold.variables)
        whole_gcode_file = whole_gcode.get()
        self._log.info(
            'job %d: verifying g-code: %s', self._job.id, whole_gcode_file)
        with open(whole_gcode_file) as whole_gcode_fp:
            for line in whole_gcode_fp:
                parser.execute_line(line)
                percent = min(100, int(parser.state.percentage))
                progress = {
                    'name': 'verify',
                    'progress': percent,
                }
                task.lazy_heartbeat(progress)
        task.end(None)

    @_task
    @_work
    def _verify_s3g_task(self, task, s3g):
        def update(percent):
            percent = min(100, int(percent))
            progress = {
                'name': 'verify',
                'progress': percent,
            }
            task.lazy_heartbeat(progress)
        s3g_file = s3g.get()
        self._log.info('job %d: verifying s3g: %d', self._job.id, s3g_file)
        reader = makerbot_driver.FileReader.FileReader()
        with open(s3g_file, 'rb') as reader.file:
            reader.ReadFile(update)
        task.end(None)

    @_task
    def _print_task(self, task, whole_gcode):
        input_file = whole_gcode.get()
        self._log.info(
            'job %d: spooling print: %s -> %s', self._job.id, input_file,
            self._job.machine.name)
        has_start_end = True
        self._spool.spool_print(
            self._job.machine, input_file, self._job.extruder_name,
            self._job.slicer_settings.extruder_temperature,
            self._job.slicer_settings.platform_temperature,
            self._job.material_name, self._job.name, task)

    @_task
    @_work
    def _copy_output_file_task(self, task, output):
        output_file = output.get()
        self._log.info(
            'job %d: copying output: %s -> %s', self._job.id, output_file,
            self._job.output_file)
        shutil.copy2(output_file, self._job.output_file)
        task.end(None)


class _Variable(object):
    def __init__(self, prefix, suffix, value=None):
        self.prefix = prefix
        self.suffix = suffix
        self._value = value

    def set(self, value):
        self._value = value

    def get(self):
        return self._value


class InvalidThingException(Exception):
    def __init__(self, path):
        Exception.__init__(self, path)
        self.path = path
