# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import conveyor.async
import conveyor.event
import unittest

class Printer(object):
    def __init__(self):
        self.progress_event = conveyor.event.Event()

    def build(self, filename):
        raise NotImplementedError

    def buildtofile(self, input_path, output_path):
        raise NotImplementedError

    def pause(self):
        raise NotImplementedError

    def unpause(self):
        raise NotImplementedError

    def stopmotion(self):
        raise NotImplementedError

    def stopall(self):
        raise NotImplementedError

class _PrinterTestCase(unittest.TestCase):
    def test_build(self):
        printer = Printer()
        with self.assertRaises(NotImplementedError):
            printer.build('filename')

    def test_buildtofile(self):
        printer = Printer()
        with self.assertRaises(NotImplementedError):
            printer.buildtofile('input_path', 'output_path')

    def test_pause(self):
        printer = Printer()
        with self.assertRaises(NotImplementedError):
            printer.pause()

    def test_unpause(self):
        printer = Printer()
        with self.assertRaises(NotImplementedError):
            printer.unpause()

    def test_stopmotion(self):
        printer = Printer()
        with self.assertRaises(NotImplementedError):
            printer.stopmotion()

    def test_stopall(self):
        printer = Printer()
        with self.assertRaises(NotImplementedError):
            printer.stopall()
