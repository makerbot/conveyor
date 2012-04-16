# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import conveyor.async
import conveyor.event
import conveyor.toolpathgenerator
import dbus
import dbus.service
import os.path
import tempfile
try:
    import unittest2 as unittest
except ImportError:
    import unittest

_TOOLPATHGENERATOR1_INTERFACE = 'com.makerbot.alpha.ToolpathGenerator1'

_TOOLPATHGENERATOR_BUS_NAME = 'com.makerbot.ToolpathGenerator'
_TOOLPATHGENERATOR_OBJECT_PATH = '/com/makerbot/ToolpathGenerator'

try: # pragma: no cover
    import dbus.mainloop.qt
    dbus.mainloop.qt.DBusQtMainLoop(set_as_default=True)
except ImportError: # pragma: no cover
    import dbus.mainloop.glib
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

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
        async = conveyor.async.asyncfunc(func)
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

class _ToolpathGeneratorTestCase(unittest.TestCase):
    def setUp(self):
        self._bus = dbus.SessionBus()
        self._stub_toolpathgenerator = _StubDbusToolpathGenerator.create(
            self._bus, _TOOLPATHGENERATOR_OBJECT_PATH,
            _TOOLPATHGENERATOR_BUS_NAME)

    def tearDown(self):
        self._stub_toolpathgenerator.remove_from_connection()

    @unittest.expectedFailure
    def test_stl_to_gcode(self):
        toolpathgenerator = _DbusToolpathGenerator.create(self._bus,
            _TOOLPATHGENERATOR_BUS_NAME)
        input = os.path.abspath('src/test/stl/single.stl')
        async = toolpathgenerator.stl_to_gcode(input)
        self.assertFalse(self._stub_toolpathgenerator.generate_callback.delivered)
        async.wait()
        # This does not work since the stub doesn't actually generate the file:
        # self.assertEqual(conveyor.async.AsyncState.SUCCESS, async.state)
        self.assertTrue(self._stub_toolpathgenerator.generate_callback.delivered)
        self.assertEqual((input,), self._stub_toolpathgenerator.generate_callback.args)
        self.assertEqual({}, self._stub_toolpathgenerator.generate_callback.kwargs)
        self.assertFalse(self._stub_toolpathgenerator.generatedualstrusion_callback.delivered)

    @unittest.expectedFailure
    def test_merge_gcode(self):
        toolpathgenerator = _DbusToolpathGenerator.create(self._bus,
            _TOOLPATHGENERATOR_BUS_NAME)
        input_filename0 = os.path.abspath('src/test/gcode/left.gcode')
        input_filename1 = os.path.abspath('src/test/gcode/right.gcode')
        output_filename = os.path.abspath('obj/merged.gcode')
        async = toolpathgenerator.merge_gcode(input_filename0,
            input_filename1, output_filename)
        self.assertFalse(self._stub_toolpathgenerator.generatedualstrusion_callback.delivered)
        async.wait()
        # This does not work since the stub doesn't actually generate the file:
        # self.assertEqual(conveyor.async.AsyncState.SUCCESS, async.state)
        self.assertTrue(self._stub_toolpathgenerator.generatedualstrusion_callback.delivered)
        self.assertEqual((input_filename0, input_filename1, output_filename),
            self._stub_toolpathgenerator.generatedualstrusion_callback.args)
        self.assertEqual({},
            self._stub_toolpathgenerator.generatedualstrusion_callback.kwargs)
        self.assertFalse(self._stub_toolpathgenerator.generate_callback.delivered)
