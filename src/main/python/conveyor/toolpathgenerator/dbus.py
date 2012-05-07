# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import PyQt4.QtCore
import dbus
import dbus.mainloop.qt
import dbus.service
import logging
import os.path
import tempfile
import threading

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import conveyor.dbus
import conveyor.event
import conveyor.task
import conveyor.toolpathgenerator

_TOOLPATHGENERATOR1_INTERFACE = 'com.makerbot.alpha.ToolpathGenerator1'

_TOOLPATHGENERATOR_BUS_NAME = 'com.makerbot.ToolpathGenerator'
_TOOLPATHGENERATOR_OBJECT_PATH = '/com/makerbot/ToolpathGenerator'

_listener = None
class _Listener(object):
    @classmethod
    def create(cls, bus):
        global _listener
        if None is _listener:
            _listener = _Listener()
            bus.add_signal_receiver(
                _listener._complete, signal_name='Complete',
                dbus_interface=_TOOLPATHGENERATOR1_INTERFACE)
        return _listener

    def __init__(self):
        self._lock = threading.Lock()
        self._task = None
        self._output = None

    def settask(self, task, output):
        with self._lock:
            if None is not self._task:
                raise Exception
            else:
                self._task = task
                self._output = output

    def _complete(self, *args, **kwargs):
        with self._lock:
            if None is not self._task:
                task = self._task
                output = self._output
                self._task = None
                self._output = None
                if not os.path.exists(output):
                    logging.error('output file does not exist: %s', output)
                    task.fail(None)
                else:
                    task.end(None)

class _DbusToolpathGenerator(conveyor.toolpathgenerator.ToolpathGenerator):
    @classmethod
    def create(cls, bus, bus_name):
        object = bus.get_object(bus_name, _TOOLPATHGENERATOR_OBJECT_PATH)
        toolpathgenerator1 = dbus.Interface(object,
            _TOOLPATHGENERATOR1_INTERFACE)
        dbustoolpathgenerator = cls(bus, bus_name, toolpathgenerator1)
        return dbustoolpathgenerator

    def __init__(self, bus, bus_name, toolpathgenerator1):
        conveyor.toolpathgenerator.ToolpathGenerator.__init__(self)
        self._bus = bus
        self._bus_name = bus_name
        self._toolpathgenerator1 = toolpathgenerator1

    def _make_task(self, label, target, output, *args):
        task = conveyor.task.Task()
        listener = _Listener.create(self._bus)
        listener.settask(task, output)
        def func(unused):
            logging.info('starting toolpathgenerator task: %s, args=%r',
                label, args)
            def reply(*args, **kwargs):
                logging.info('reply: args=%r, kwargs=%r', args, kwargs)
            def error(*args, **kwargs):
                logging.info('error: args=%r, kwargs=%r', args, kwargs)
                task.fail(None)
            target(*args, reply_handler=reply, error_handler=error)
        task.runningevent.attach(func)
        return task

    def stl_to_gcode(self, input):
        output = _gcode_filename(input)
        task = self._make_task('Generate',
            self._toolpathgenerator1.Generate, output, input)
        return task

    def merge_gcode(self, input_left, input_right, output):
        task = self._make_task('GenerateDualStrusion',
            self._toolpathgenerator1.GenerateDualStrusion, output, input_left,
            input_right, output)
        return task

class _StubDbusToolpathGenerator(dbus.service.Object):
    @classmethod
    def create(cls, bus, object_path, bus_name):
        conn = dbus.service.BusName(bus_name, bus)
        toolpathgenerator = _StubDbusToolpathGenerator(conn, object_path)
        return toolpathgenerator

    def __init__(self, conn, object_path):
        dbus.service.Object.__init__(self, conn, object_path)
        self.generate_callback = conveyor.event.Callback()
        self.generatedualstrusion_callback = conveyor.event.Callback()

    @dbus.service.method(dbus_interface=_TOOLPATHGENERATOR1_INTERFACE,
        in_signature='s', out_signature='')
    def Generate(self, filename):
        self.generate_callback(unicode(filename))
        self.Progress()
        self.Complete()

    @dbus.service.method(dbus_interface=_TOOLPATHGENERATOR1_INTERFACE,
        in_signature='sss', out_signature='')
    def GenerateDualStrusion(self, input_filename0, input_filename1,
        output_filename):
            self.generatedualstrusion_callback(unicode(input_filename0),
                unicode(input_filename1), unicode(output_filename))
            self.Progress()
            self.Complete()

    @dbus.service.signal(dbus_interface=_TOOLPATHGENERATOR1_INTERFACE,
        signature='')
    def Progress(self):
        pass

    @dbus.service.signal(dbus_interface=_TOOLPATHGENERATOR1_INTERFACE,
        signature='')
    def Complete(self):
        pass

def _gcode_filename(stl, testcase=None):
    assert stl.endswith('.stl')
    gcode = ''.join((stl[:-4], '.gcode'))
    return gcode

class _ToolpathGeneratorTestCase(conveyor.dbus.DbusTestCase):
    def setUp(self):
        self._bus = dbus.SessionBus()
        self._stub_toolpathgenerator = _StubDbusToolpathGenerator.create(
            self._bus, _TOOLPATHGENERATOR_OBJECT_PATH,
            _TOOLPATHGENERATOR_BUS_NAME)

    def tearDown(self):
        self._stub_toolpathgenerator.remove_from_connection()

    def test_stl_to_gcode(self):
        toolpathgenerator = _DbusToolpathGenerator.create(self._bus,
            _TOOLPATHGENERATOR_BUS_NAME)
        input = os.path.abspath('src/test/stl/single.stl')
        task = toolpathgenerator.stl_to_gcode(input)
        self.assertFalse(self._stub_toolpathgenerator.generate_callback.delivered)
        self._wait(task)
        self.assertEqual(conveyor.task.TaskState.STOPPED, task.state)
        # This does not work since the stub doesn't actually generate the file:
        # self.assertEqual(conveyor.task.TaskConclusion.ENDED, task.conclusion)
        self.assertTrue(self._stub_toolpathgenerator.generate_callback.delivered)
        self.assertEqual((input,), self._stub_toolpathgenerator.generate_callback.args)
        self.assertEqual({}, self._stub_toolpathgenerator.generate_callback.kwargs)
        self.assertFalse(self._stub_toolpathgenerator.generatedualstrusion_callback.delivered)

    def test_merge_gcode(self):
        toolpathgenerator = _DbusToolpathGenerator.create(self._bus,
            _TOOLPATHGENERATOR_BUS_NAME)
        input_filename0 = os.path.abspath('src/test/gcode/left.gcode')
        input_filename1 = os.path.abspath('src/test/gcode/right.gcode')
        output_filename = os.path.abspath('obj/merged.gcode')
        task = toolpathgenerator.merge_gcode(input_filename0,
            input_filename1, output_filename)
        self.assertFalse(self._stub_toolpathgenerator.generatedualstrusion_callback.delivered)
        self._wait(task)
        self.assertEqual(conveyor.task.TaskState.STOPPED, task.state)
        # This does not work since the stub doesn't actually generate the file:
        # self.assertEqual(conveyor.task.TaskConclusion.ENDED, task.conclusion)
        self.assertTrue(self._stub_toolpathgenerator.generatedualstrusion_callback.delivered)
        self.assertEqual((input_filename0, input_filename1, output_filename),
            self._stub_toolpathgenerator.generatedualstrusion_callback.args)
        self.assertEqual({},
            self._stub_toolpathgenerator.generatedualstrusion_callback.kwargs)
        self.assertFalse(self._stub_toolpathgenerator.generate_callback.delivered)
