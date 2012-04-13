# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import conveyor.async
import conveyor.printer
import dbus
import dbus.service
import os.path
import tempfile
import unittest

_PRINTER1_INTERFACE = 'com.makerbot.alpha.Printer1'

_PRINTER_BUS_NAME = 'com.makerbot.Printer'
_PRINTER_OBJECT_PATH = '/com/makerbot/Printer'

try: # pragma: no cover
    import dbus.mainloop.qt
    dbus.mainloop.qt.DBusQtMainLoop(set_as_default=True)
except ImportError: # pragma: no cover
    import dbus.mainloop.glib
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

class _DbusPrinter(conveyor.printer.Printer):
    @classmethod
    def create(cls, bus, bus_name):
        object = bus.get_object(bus_name, _PRINTER_OBJECT_PATH)
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

class _StubDbusPrinter(dbus.service.Object):
    @classmethod
    def create(cls, bus, object_path, bus_name):
        conn = dbus.service.BusName(bus_name, bus)
        printer = _StubDbusPrinter(conn, object_path)
        return printer

    def __init__(self, conn, object_path):
        dbus.service.Object.__init__(self, conn, object_path)
        self.build_callback = conveyor.event.Callback()
        self.buildtofile_callback = conveyor.event.Callback()
        self.pause_callback = conveyor.event.Callback()
        self.unpause_callback = conveyor.event.Callback()
        self.stopmotion_callback = conveyor.event.Callback()
        self.stopall_callback = conveyor.event.Callback()

    @dbus.service.method(dbus_interface=_PRINTER1_INTERFACE, in_signature='s',
        out_signature='')
    def Build(self, filename):
        self.build_callback(unicode(filename))

    @dbus.service.method(dbus_interface=_PRINTER1_INTERFACE,
        in_signature='ss', out_signature='')
    def BuildToFile(self, input_path, output_path):
        self.buildtofile_callback(unicode(input_path), unicode(output_path))

    @dbus.service.method(dbus_interface=_PRINTER1_INTERFACE, in_signature='',
        out_signature='')
    def Pause(self):
        self.pause_callback()

    @dbus.service.method(dbus_interface=_PRINTER1_INTERFACE, in_signature='',
        out_signature='')
    def Unpause(self):
        self.unpause_callback()

    @dbus.service.method(dbus_interface=_PRINTER1_INTERFACE, in_signature='',
        out_signature='')
    def StopMotion(self):
        self.stopmotion_callback()

    @dbus.service.method(dbus_interface=_PRINTER1_INTERFACE, in_signature='',
        out_signature='')
    def StopAll(self):
        self.stopall_callback()

class _DbusPrinterTestCase(unittest.TestCase):
    def setUp(self):
        self._bus = dbus.SessionBus()
        self._stub_printer = _StubDbusPrinter.create(self._bus,
            _PRINTER_OBJECT_PATH, _PRINTER_BUS_NAME)

    def tearDown(self):
        self._stub_printer.remove_from_connection()
        pass

    @unittest.expectedFailure
    def test_build(self):
        printer = _DbusPrinter.create(self._bus, _PRINTER_BUS_NAME)
        filename = os.path.abspath('src/test/gcode/single.gcode')
        async = printer.build(filename)
        self.assertFalse(self._stub_printer.build_callback.delivered)
        async.wait()
        self.assertEqual(conveyor.async.AsyncState.SUCCESS, async.state)
        self.assertTrue(self._stub_printer.build_callback.delivered)
        self.assertEqual((filename,), self._stub_printer.build_callback.args)
        self.assertEqual({}, self._stub_printer.build_callback.kwargs)
        for callback in (self._stub_printer.buildtofile_callback,
            self._stub_printer.pause_callback,
            self._stub_printer.unpause_callback,
            self._stub_printer.stopmotion_callback,
            self._stub_printer.stopall_callback):
                self.assertFalse(callback.delivered)

    @unittest.expectedFailure
    def test_buildtofile(self):
        printer = _DbusPrinter.create(self._bus, _PRINTER_BUS_NAME)
        input_path = os.path.abspath('src/test/gcode/single.gcode')
        output_path = os.path.abspath('obj/single.s3g')
        async = printer.buildtofile(input_path, output_path)
        self.assertFalse(self._stub_printer.buildtofile_callback.delivered)
        async.wait()
        self.assertEqual(conveyor.async.AsyncState.SUCCESS, async.state)
        self.assertTrue(self._stub_printer.buildtofile_callback.delivered)
        self.assertEqual((input_path, output_path,),
            self._stub_printer.buildtofile_callback.args)
        self.assertEqual({}, self._stub_printer.buildtofile_callback.kwargs)
        for callback in (self._stub_printer.build_callback,
            self._stub_printer.pause_callback,
            self._stub_printer.unpause_callback,
            self._stub_printer.stopmotion_callback,
            self._stub_printer.stopall_callback):
                self.assertFalse(callback.delivered)

    @unittest.expectedFailure
    def test_pause(self):
        printer = _DbusPrinter.create(self._bus, _PRINTER_BUS_NAME)
        async = printer.pause()
        self.assertFalse(self._stub_printer.pause_callback.delivered)
        async.wait()
        self.assertEqual(conveyor.async.AsyncState.SUCCESS, async.state)
        self.assertTrue(self._stub_printer.pause_callback.delivered)
        self.assertEqual((), self._stub_printer.pause_callback.args)
        self.assertEqual({}, self._stub_printer.pause_callback.kwargs)
        for callback in (self._stub_printer.build_callback,
            self._stub_printer.buildtofile_callback,
            self._stub_printer.unpause_callback,
            self._stub_printer.stopmotion_callback,
            self._stub_printer.stopall_callback):
                self.assertFalse(callback.delivered)

    @unittest.expectedFailure
    def test_unpause(self):
        printer = _DbusPrinter.create(self._bus, _PRINTER_BUS_NAME)
        async = printer.unpause()
        self.assertFalse(self._stub_printer.unpause_callback.delivered)
        async.wait()
        self.assertEqual(conveyor.async.AsyncState.SUCCESS, async.state)
        self.assertTrue(self._stub_printer.unpause_callback.delivered)
        self.assertEqual((), self._stub_printer.unpause_callback.args)
        self.assertEqual({}, self._stub_printer.unpause_callback.kwargs)
        for callback in (self._stub_printer.build_callback,
            self._stub_printer.buildtofile_callback,
            self._stub_printer.pause_callback,
            self._stub_printer.stopmotion_callback,
            self._stub_printer.stopall_callback):
                self.assertFalse(callback.delivered)

    @unittest.expectedFailure
    def test_stopmotion(self):
        printer = _DbusPrinter.create(self._bus, _PRINTER_BUS_NAME)
        async = printer.stopmotion()
        self.assertFalse(self._stub_printer.stopmotion_callback.delivered)
        async.wait()
        self.assertEqual(conveyor.async.AsyncState.SUCCESS, async.state)
        self.assertTrue(self._stub_printer.stopmotion_callback.delivered)
        self.assertEqual((), self._stub_printer.stopmotion_callback.args)
        self.assertEqual({}, self._stub_printer.stopmotion_callback.kwargs)
        for callback in (self._stub_printer.build_callback,
            self._stub_printer.buildtofile_callback,
            self._stub_printer.pause_callback,
            self._stub_printer.unpause_callback,
            self._stub_printer.stopall_callback):
                self.assertFalse(callback.delivered)

    @unittest.expectedFailure
    def test_stopall(self):
        printer = _DbusPrinter.create(self._bus, _PRINTER_BUS_NAME)
        async = printer.stopall()
        self.assertFalse(self._stub_printer.stopall_callback.delivered)
        async.wait()
        self.assertEqual(conveyor.async.AsyncState.SUCCESS, async.state)
        self.assertTrue(self._stub_printer.stopall_callback.delivered)
        self.assertEqual((), self._stub_printer.stopall_callback.args)
        self.assertEqual({}, self._stub_printer.stopall_callback.kwargs)
        for callback in (self._stub_printer.build_callback,
            self._stub_printer.buildtofile_callback,
            self._stub_printer.pause_callback,
            self._stub_printer.unpause_callback,
            self._stub_printer.stopmotion_callback):
                self.assertFalse(callback.delivered)
