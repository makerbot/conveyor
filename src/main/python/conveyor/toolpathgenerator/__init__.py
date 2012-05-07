# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:

from __future__ import (absolute_import, print_function, unicode_literals)

import conveyor.event

try:
    import unittest2 as unittest
except ImportError:
    import unittest

class ToolpathGenerator(object):
    def __init__(self):
        self.progress_event = conveyor.event.Event('ToolpathGenerator.progressevent')
        self.complete_event = conveyor.event.Event('ToolpathGenerator.completeevent')

    def stl_to_gcode(self, filename):
        raise NotImplementedError

    def merge_gcode(self, input_left, input_right, output):
        raise NotImplementedError

class _ToolpathGeneratorTestCase(unittest.TestCase):
    def test_stl_to_gcode(self):
        toolpathgenerator = ToolpathGenerator()
        with self.assertRaises(NotImplementedError):
            toolpathgenerator.stl_to_gcode('single.stl')

    def test_merge_gcode(self):
        toolpathgenerator = ToolpathGenerator()
        with self.assertRaises(NotImplementedError):
            toolpathgenerator.merge_gcode('left.gcode', 'right.gcode',
                'merged.gcode')
