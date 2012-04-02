# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import conveyor.async
import conveyor.async.glib
import conveyor.toolpathgenerator
import dbus
import gobject
import os.path
import tempfile
import unittest

import dbus.mainloop.glib
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

_TOOLPATHGENERATOR1_INTERFACE = 'com.makerbot.alpha.ToolpathGenerator1'

class _DbusToolpathGenerator(conveyor.toolpathgenerator.ToolpathGenerator):
    @classmethod
    def create(cls, bus, bus_name):
        object = bus.get_object(bus_name, '/com/makerbot/ToolpathGenerator')
        toolpathgenerator1 = dbus.Interface(object,
            _TOOLPATHGENERATOR1_INTERFACE)
        dbustoolpathgenerator = cls(bus, bus_name, toolpathgenerator1)
        return dbustoolpathgenerator

    def __init__(self, bus, bus_name, toolpathgenerator1):
        conveyor.toolpathgenerator.ToolpathGenerator.__init__(self)
        self._bus = bus
        self._bus_name = bus_name
        self._toolpathgenerator1 = toolpathgenerator1

    def _make_async(self, target, output, *args):
        def func(async):
            self._bus.add_signal_receiver(async.heartbeat_trigger,
                signal_name='Progress',
                dbus_interface=_TOOLPATHGENERATOR1_INTERFACE)
            def complete(*args, **kwargs):
                if not os.path.exists(output):
                    async.error_trigger()
                else:
                    async.reply_trigger()
            self._bus.add_signal_receiver(complete,
                signal_name='Complete',
                dbus_interface=_TOOLPATHGENERATOR1_INTERFACE)
            def reply(*args, **kwargs):
                pass
            target(*args, reply_handler=reply,
                error_handler=async.error_trigger)
        async = conveyor.async.glib.fromfunc(func)
        return async

    def stl_to_gcode(self, input):
        output = _gcode_filename(input)
        async = self._make_async(self._toolpathgenerator1.Generate, output,
            input)
        return async

    def merge_gcode(self, input_left, input_right, output):
        async = self._make_async(
            self._toolpathgenerator1.GenerateDualStrusion, output, input_left,
            input_right, output)
        return async

def _gcode_filename(stl, testcase=None):
    if None != testcase:
        testcase.assertTrue(stl.endswith('.stl'))
    gcode = ''.join((stl[:-4], '.gcode'))
    return gcode

def _unlink(path):
    if os.path.exists(path):
        os.unlink(path)

def _stl_to_gcode(testcase, toolpathgenerator, input):
    output = _gcode_filename(input, testcase)
    _unlink(output)
    testcase.assertFalse(os.path.exists(output))
    async = toolpathgenerator.stl_to_gcode(input)
    async.wait()
    testcase.assertEqual(conveyor.async.AsyncState.SUCCESS, async.state)
    testcase.assertTrue(os.path.exists(output))

class _ToolpathGeneratorSingleTestCase(unittest.TestCase):
    def setUp(self):
        self.input = os.path.abspath('src/test/stl/single.stl')
        self.output = _gcode_filename(self.input, self)

    def tearDown(self):
        _unlink(self.output)

    def test_single(self):
        bus = dbus.SessionBus()
        bus_name = 'com.makerbot.ToolpathGenerator0'
        toolpathgenerator = _DbusToolpathGenerator.create(bus, bus_name)
        _stl_to_gcode(self, toolpathgenerator, self.input)

class _ToolpathGeneratorDualstrusionTestCase(unittest.TestCase):
    def setUp(self):
        self.stl_left = os.path.abspath('src/test/stl/left.stl')
        self.input_left = _gcode_filename(self.stl_left, self)
        self.stl_right = os.path.abspath('src/test/stl/right.stl')
        self.input_right = _gcode_filename(self.stl_right, self)
        with tempfile.NamedTemporaryFile(delete=False) as temporary:
            self.output = temporary.name
        _unlink(self.output)

    def tearDown(self):
        _unlink(self.input_left)
        _unlink(self.input_right)
        _unlink(self.output)

    def test_dualstrusion(self):
        bus = dbus.SessionBus()
        bus_name = 'com.makerbot.ToolpathGenerator0'
        toolpathgenerator = _DbusToolpathGenerator.create(bus, bus_name)
        _stl_to_gcode(self, toolpathgenerator, self.stl_left)
        _stl_to_gcode(self, toolpathgenerator, self.stl_right)
        self.assertFalse(os.path.exists(self.output))
        async = toolpathgenerator.merge_gcode(self.input_left,
            self.input_right, self.output)
        async.wait()
        self.assertEqual(conveyor.async.AsyncState.SUCCESS, async.state)
        self.assertTrue(os.path.exists(self.output))
