# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import conveyor.async
import conveyor.printer
import conveyor.test
import dbus
import os.path
import tempfile
import unittest

_PRINTER1_INTERFACE = 'com.makerbot.alpha.Printer1'

import dbus.mainloop.qt
dbus.mainloop.qt.DBusQtMainLoop(set_as_default=True)

class _DbusPrinter(conveyor.printer.Printer):
    @classmethod
    def create(cls, bus, bus_name):
        object = bus.get_object(bus_name, '/com/makerbot/Printer')
        printer1 = dbus.Interface(object, _PRINTER1_INTERFACE)
        dbusprinter = cls(bus, bus_name, printer1)
        return dbusprinter

    def __init__(self, bus, bus_name, printer1):
        conveyor.printer.Printer.__init__(self)
        self._bus = bus
        self._bus_name = bus_name
        self._printer1 = printer1

    def _make_async(self, target, *args):
        def func(async):
            target(*args, reply_handler=async.reply_trigger,
                error_handler=async.error_trigger)
        async = conveyor.async.asyncfunc(func)
        return async

    def build(self, filename):
        async = self._make_async(self._printer1.Build, filename)
        return async

    def buildtofile(self, input_path, output_path):
        async = self._make_async(self._printer1.BuildToFile, input_path,
            output_path)
        return async

    def pause(self):
        async = self._make_async(self._printer1.Pause)
        return async

    def unpause(self):
        async = self._make_async(self._printer1.Unpause)
        return async

    def stopmotion(self):
        async = self._make_async(self._printer1.StopMotion)
        return async

    def stopall(self):
        async = self._make_async(self._printer1.StopAll)
        return async

def _unlink(path):
    if os.path.exists(path):
        os.unlink(path)

class _DbusPrinter_build_TestCase(unittest.TestCase):
    @unittest.skipIf(conveyor.test.skipIntegrationTests, 'integration test')
    def test_build(self):
        bus = dbus.SessionBus()
        bus_name = 'com.makerbot.Printer'
        printer = _DbusPrinter.create(bus, bus_name)
        filename = os.path.abspath('src/test/gcode/single.gcode')
        async = printer.build(filename)
        printer.progress_event.attach(async.heartbeat_trigger)
        async.wait()
        self.assertEqual(conveyor.async.AsyncState.SUCCESS, async.state)

    @unittest.skipIf(conveyor.test.skipIntegrationTests, 'integration test')
    @unittest.expectedFailure # virtual printer doesn't support build-to-file
    def test_buildtofile(self):
        bus = dbus.SessionBus()
        bus_name = 'com.makerbot.Printer'
        printer = _DbusPrinter.create(bus, bus_name)
        input_path = os.path.abspath('src/test/gcode/single.gcode')
        with tempfile.NamedTemporaryFile(delete=False) as temporary:
            output_path = temporary.name
        _unlink(output_path)
        try:
            async = printer.buildtofile(input_path, output_path)
            async.wait()
            self.assertEqual(conveyor.async.AsyncState.SUCCESS, async.state)
            self.assertTrue(os.path.exists(output_path))
        finally:
            _unlink(output_path)
