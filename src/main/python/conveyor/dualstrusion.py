from __future__ import print_function

import os
import sys
path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    '../../../../../',
    's3g',
)
sys.path.insert(0, path)

import re
import collections
import mock
import unittest
import makerbot_driver
import conveyor

class DualstrusionWeaver(object):

    def __init__(self, tool_0_codes, tool_1_codes, task):
        self.tool_0_codes = tool_0_codes
        self.tool_1_codes = tool_1_codes
        self.task = task
        self.last_position_0 = None
        self.next_position_0 = None
        self.last_position_1 = None
        self.next_position_1 = None
        self.last_used_codes = self.tool_0_codes
        tool_0_length = len(self.tool_0_codes.gcodes)
        tool_1_length = len(self.tool_1_codes.gcodes)
        self.total_length = tool_0_length + tool_1_length
        self.new_codes = []
        self.next_location_regex = re.compile("[gG]1.*?[zZ][-]?([\d]*\.?[\d]+)")
        self.last_location_regex = re.compile("[gG]1.*?[xXyY][-]?([\d]*\.?[\d]+)")
        self.percent = 0

    def get_toolchange_commands(self, tool_codes):
        commands = []
        if tool_codes == self.tool_0_codes:
            tool = 0
            transition_codes = self.create_transition_location(self.last_position_0, self.next_position_0)
        else:
            tool = 1
            transition_codes = self.create_transition_location(self.last_position_1, self.next_position_1)
        toolchange = "M135 T%i\n" % (tool)
        commands.append(toolchange)
        commands.extend(transition_codes)
        return commands

    def combine_codes(self):
        self.task.lazy_heartbeat(self.percent)
        while len(self.tool_0_codes.gcodes) is not 0 or len(self.tool_1_codes.gcodes) is not 0:
            if conveyor.task.TaskState.RUNNING != self.task.state:
                self.task.fail(None)
                break
            next_gcode_obj = self.get_next_code_list()
            next_layer = self.get_next_layer(next_gcode_obj)
            self.set_next_location(next_layer, next_gcode_obj)
            toolchange_codes = self.get_toolchange_commands(next_gcode_obj)
            self.new_codes.extend(toolchange_codes)
            self.new_codes.extend(next_layer)
            self.set_last_location(next_layer, next_gcode_obj)
            new_percent = min(int(len(self.new_codes) / float(self.total_length) * 100), 99)
            self.task.lazy_heartbeat(new_percent, self.percent)
            self.percent = new_percent
        if conveyor.task.TaskState.RUNNING == self.task.state:
            self.task.lazy_heartbeat(100, self.percent)
        return self.new_codes

    @staticmethod
    def create_transition_location(previous_point, next_point):
        all_codes = []
        if previous_point:
            prev_codes = makerbot_driver.Gcode.parse_line(previous_point)[0]
            # Attribute errors mean these commands are None.  We will try to recover though to produce something usable
            try:
                next_codes = makerbot_driver.Gcode.parse_line(next_point)[0]
            except AttributeError as e:
                next_codes = {}
            trans_code = "G1"
            for axis in ['X', 'Y']:
                if axis in prev_codes:
                    trans_code += " %s"  % (axis) + str(prev_codes[axis])
            for axis in ['Z']:
                if axis in next_codes:
                    trans_code += " %s"  % (axis) + str(next_codes[axis])
            trans_code += '\n'
            if 'X' in trans_code or 'Y' in trans_code or 'Z' in trans_code:
                all_codes.append(trans_code)
        return all_codes

    def set_next_location(self, codes, gcode_obj):
        for code in codes:
            if re.match(self.next_location_regex, code):
                if gcode_obj == self.tool_0_codes:
                    self.next_position_0 = code
                else:
                    self.next_position_1 = code
                break

    def set_last_location(self, codes, gcode_obj):
        codes.reverse()
        for code in codes:
            if re.match(self.last_location_regex, code):
                if gcode_obj == self.tool_0_codes:
                    self.last_position_0 = code
                else:
                    self.last_position_1 = code
                break

    def get_next_code_list(self):
        tool_0_height = self.tool_0_codes.peek_next_layer_height()
        tool_1_height = self.tool_1_codes.peek_next_layer_height()
        if len(self.tool_0_codes.gcodes) == 0:
            self.last_used_codes = self.tool_1_codes
        elif len(self.tool_1_codes.gcodes) == 0:
            self.last_used_codes = self.tool_0_codes
        elif tool_0_height < tool_1_height:
            self.last_used_codes = self.tool_0_codes
        elif tool_1_height < tool_0_height:
            self.last_used_codes = self.tool_1_codes
        return self.last_used_codes

    def get_next_layer(self, gcode_obj):
        return gcode_obj.get_next_layer()

class GcodeObject(object):

    def __init__(self, gcodes=[]):
        self.gcodes = collections.deque(gcodes)
        #self.skeinforge_tag = re.compile("\(</layer>\)")
        #self.miraclegrue_tag = re.compile("\(Slice (\d+), (\d+) Extruder\)")
        self.layer_tag = re.compile("\(</layer>\)|\(Slice (\d+), (\d+) Extruder\)")
        self.layer_height_regex = re.compile("[gG]1.*?[zZ]([\d]*\.?[\d]+)")
        self.last_layer_height = 0

    def peek_next_layer_height(self):
        for code in self.gcodes:
            the_match = re.match(self.layer_height_regex, code)
            if the_match:
                next_height = float(the_match.group(1))
                self.last_layer_height = next_height
                break
            # If we encounter the next layer height, and no Z height was found, break and return
            # the last layer height found
            if re.match(self.layer_tag, code):
                break
        return self.last_layer_height

    def get_next_layer(self):
        layer = []
        for line in self.gcodes:
            layer.append(line)
            if re.match(self.layer_tag, line):
                break
        for i in range(len(layer)):
            self.gcodes.popleft()
        return layer

class TestGcodeObject(unittest.TestCase):

    def setUp(self):
        self.gcode_obj = GcodeObject()

    def tearDown(self):
        self.gcode_obj = None

    def test_peek_next_layer_height_zero_prefixed_decimal(self):
        gcodes = [
            "M134 T0",
            "G92 X0 Y0 Z0 A0 B0",
            "G92 Z500",
            "G1 X0 Y0 Z1.05",
            "G1 X0 Y0 Z1",
            "G1 X0 Y0 Z20",
        ]
        self.gcode_obj.gcodes = collections.deque(gcodes)
        expected_next = 1.05
        self.assertEqual(expected_next, self.gcode_obj.peek_next_layer_height())

    def test_peek_next_layer_height_int(self):
        gcodes = [
            "M134 T0",
            "G92 X0 Y0 Z0 A0 B0",
            "G92 Z500",
            "G1 X0 Y0 Z5",
            "G1 X0 Y0 Z1",
            "G1 X0 Y0 Z20",
        ]
        self.gcode_obj.gcodes = collections.deque(gcodes)
        expected_next = 5
        self.assertEqual(expected_next, self.gcode_obj.peek_next_layer_height())

    def test_peek_next_layer_height_decimal(self):
        gcodes = [
            "M134 T0",
            "G92 X0 Y0 Z0 A0 B0",
            "G92 Z500",
            "G1 X0 Y0 Z.5",
            "G1 X0 Y0 Z1",
            "G1 X0 Y0 Z20",
        ]
        self.gcode_obj.gcodes = collections.deque(gcodes)
        expected_next = .5
        self.assertEqual(expected_next, self.gcode_obj.peek_next_layer_height())

    def test_peek_next_layer_height_no_layer_height(self):
        gcodes = [
            "M134 T0",
            "G92 X0 Y0 Z0",
            "G1 X0 Y0 A0",
            "M99",
        ]
        self.gcode_obj.gcodes = collections.deque(gcodes)
        expected_next = 0
        self.assertEqual(expected_next, self.gcode_obj.peek_next_layer_height())

    def test_peek_next_layer_height_no_layer_height_in_layer(self):
        gcodes = [
            "G1 Z.5",
            "(Slice 0, 5 Extruder)",
            "M135",
            "G92 X0 Y0",
            "(Slice 0, 5 Extruder)",
        ]
        self.gcode_obj.gcodes = collections.deque(gcodes[:])
        expected_first_layer_height = .5
        self.assertEqual(expected_first_layer_height, self.gcode_obj.peek_next_layer_height())
        self.gcode_obj.get_next_layer()
        self.assertEqual(expected_first_layer_height, self.gcode_obj.peek_next_layer_height())

    def test_get_next_layer_skeinforge(self):
        gcodes = [
            "M134 T0",
            "G1 X0 Y0 Z0",
            "G92 X0 Y0 Z50",
            "M99",
            "(some interesting comments)",
            "(</layer>)",
            "<layer>",
            "G1 X1 Y2 Z3",
            "G92 X100 Y100 Z100 A100",
            "(</layer>)",
        ]
        self.gcode_obj.gcodes = collections.deque(gcodes[:])
        expected_layer = [
            "M134 T0",
            "G1 X0 Y0 Z0",
            "G92 X0 Y0 Z50",
            "M99",
            "(some interesting comments)",
            "(</layer>)"
        ]
        expected_leftovers = collections.deque(gcodes[6:])
        self.assertEqual(expected_layer, self.gcode_obj.get_next_layer())
        self.assertEqual(len(self.gcode_obj.gcodes), len(gcodes) - len(expected_layer))
        self.assertEqual(expected_leftovers, self.gcode_obj.gcodes)

    def test_get_next_layer_miraclegrue(self):
        gcodes = [
            "M134 T0",
            "G1 X0 Y0 Z0",
            "G92 X0 Y0 Z50",
            "M99",
            "(some interesting comments)",
            "(Slice 54, 3 Extruder)",
            "G1 X1 Y2 Z3",
            "G92 X100 Y100 Z100 A100",
            ]
        self.gcode_obj.gcodes = collections.deque(gcodes[:])
        expected_layer = [
            "M134 T0",
            "G1 X0 Y0 Z0",
            "G92 X0 Y0 Z50",
            "M99",
            "(some interesting comments)",
            "(Slice 54, 3 Extruder)",
        ]
        expected_leftovers = collections.deque(gcodes[6:])
        self.assertEqual(expected_layer, self.gcode_obj.get_next_layer())
        self.assertEqual(len(self.gcode_obj.gcodes), len(gcodes) - len(expected_layer))
        self.assertEqual(expected_leftovers, self.gcode_obj.gcodes)

    def test_get_next_layer_no_layer_tag(self):
        gcodes = [
            "M134 T0",
            "G1 X0 Y0 Z0",
            "G92 X0 Y0 Z50",
            "M99",
            "(some interesting comments)",
            "G1 X1 Y2 Z3",
            "G92 X100 Y100 Z100 A100",
            ]
        self.gcode_obj.gcodes = collections.deque(gcodes[:])
        expected_layer = [
            "M134 T0",
            "G1 X0 Y0 Z0",
            "G92 X0 Y0 Z50",
            "M99",
            "(some interesting comments)",
            "G1 X1 Y2 Z3",
            "G92 X100 Y100 Z100 A100",
        ]
        expected_leftovers = collections.deque([])
        self.assertEqual(expected_layer, self.gcode_obj.get_next_layer())
        self.assertEqual(len(self.gcode_obj.gcodes), len(expected_layer) - len(gcodes))
        self.assertEqual(expected_leftovers, self.gcode_obj.gcodes)

class TestDualstrusionWeaver(unittest.TestCase):

    def test_combine_codes(self):
        t0_codes = [
            "<layer>",
            "M132",
            "G92 X0 Y0 Z0 A0 B0",
            "G1 X50 Y50 Z1.05",
            "(</layer>)",
            "<layer>",
            "M132",
            "G1 X0 Y0 Z1.5",
            "G92 X99 Y99",
            "(</layer>)",
        ]
        t1_codes = [
            "G1 X1 Y2 Z1.05",
            "G1 X59 Y58",
            "M132",
            "G92",
            "(Slice 54, 3 Extruder)",
            "G1 X1 Y2 Z1.5",
            "G99",
            "M101",
            "M105",
            "(Slice 55, 3 Extruder)",
        ]
        expected_gcodes = [
            "M135 T0\n",
            "<layer>",
            "M132",
            "G92 X0 Y0 Z0 A0 B0",
            "G1 X50 Y50 Z1.05",
            "(</layer>)",
            "M135 T1\n",
            "G1 X1 Y2 Z1.05",
            "G1 X59 Y58",
            "M132",
            "G92",
            "(Slice 54, 3 Extruder)",
            "M135 T1\n",
            "G1 X59 Y58 Z1.5\n",
            "G1 X1 Y2 Z1.5",
            "G99",
            "M101",
            "M105",
            "(Slice 55, 3 Extruder)",
            "M135 T0\n",
            "G1 X50 Y50 Z1.5\n",
            "<layer>",
            "M132",
            "G1 X0 Y0 Z1.5",
            "G92 X99 Y99",
            "(</layer>)",
        ]
        tool_0_codes = GcodeObject(gcodes=t0_codes)
        tool_1_codes = GcodeObject(gcodes=t1_codes)
        weaver = DualstrusionWeaver(tool_0_codes, tool_1_codes)
        result = weaver.combine_codes()
        self.assertEqual(expected_gcodes, result)

    def test_get_next_layer(self):
        t0_codes = [
            "<layer>",
            "M132",
            "G92 X0 Y0 Z0 A0 B0",
            "G1 X50 Y50 Z50",
            "(</layer>)",
            "<layer>",
            "M132",
            "G1 X0 Y0 Z0",
            "G92 X99 Y99:",
            "(</layer>)",
            ]
        expected_t0_codes = t0_codes[:5]
        expected_leftovers = collections.deque(t0_codes[5:])
        tool_0_codes = GcodeObject(gcodes=t0_codes[:])
        tool_1_codes = GcodeObject(gcodes=[])
        weaver = DualstrusionWeaver(tool_0_codes, tool_1_codes)
        self.assertEqual(expected_t0_codes, weaver.get_next_layer(tool_0_codes))
        self.assertEqual(expected_leftovers, tool_0_codes.gcodes)

    def test_get_next_code_list_equal_height(self):
        codes = [
            "<layer>",
            "G1 Z1.05",
            "(</layer>)",
            "<layer>",
            "G1 Z1.5",
            "(</layer>)",
            "<layer>",
            "G1 Z2.05",
            "(</layer>)",
        ]
            
        t0_codes = GcodeObject(codes[:])
        t1_codes = GcodeObject(codes[:])
        weaver = DualstrusionWeaver(t0_codes, t1_codes)

        expected_results = [t0_codes, t1_codes, t1_codes, t0_codes, t0_codes, t1_codes]

        for expected in expected_results:
            got_next = weaver.get_next_code_list()
            self.assertEqual(got_next, expected)
            self.assertEqual(weaver.last_used_codes, expected)
            got_next.get_next_layer()

    def test_get_toolchange_commands(self):
        t0_codes = GcodeObject([])
        t1_codes = GcodeObject([])
        weaver = DualstrusionWeaver(t0_codes, t1_codes)
        expected_toolchange_command = [
            "M135 T0\n"
        ]
        self.assertEqual(expected_toolchange_command, weaver.get_toolchange_commands(t0_codes))

    def test_get_toolchange_commands_with_last_used_t0(self):
        t0_codes = GcodeObject([])
        t1_codes = GcodeObject([])
        weaver = DualstrusionWeaver(t0_codes, t1_codes)
        weaver.last_position_0 = 'G1 X50 Y50'
        weaver.next_position_0 = 'G1 X0 Y0 Z500'
        weaver.last_position_1 = 'G1 X100 Y100'
        weaver.next_position_1 = 'G1 X0 Y0 Z400'
        expected_toolchange_command = [
            "M135 T0\n",
            "G1 X50 Y50 Z500\n",
        ]
        self.assertEqual(expected_toolchange_command, weaver.get_toolchange_commands(t0_codes))

    def test_get_toolchange_commands_with_last_used_t1(self):
        t0_codes = GcodeObject([])
        t1_codes = GcodeObject([])
        weaver = DualstrusionWeaver(t0_codes, t1_codes)
        weaver.last_position_0 = 'G1 X50 Y50'
        weaver.next_position_0 = 'G1 X0 Y0 Z500'
        weaver.last_position_1 = 'G1 X100 Y100'
        weaver.next_position_1 = 'G1 X0 Y0 Z400'
        expected_toolchange_command = [
            "M135 T1\n",
            "G1 X100 Y100 Z400\n",
        ]
        self.assertEqual(expected_toolchange_command, weaver.get_toolchange_commands(t1_codes))

    def test_get_toolchange_commands_with_last_used_t0_last_none(self):
        t0_codes = GcodeObject([])
        t1_codes = GcodeObject([])
        weaver = DualstrusionWeaver(t0_codes, t1_codes)
        weaver.last_position_0 = None
        weaver.next_position_0 = 'G1 X0 Y0 Z500'
        weaver.last_position_1 = 'G1 X100 Y100'
        weaver.next_position_1 = 'G1 X0 Y0 Z400'
        expected_toolchange_command = [
            "M135 T0\n",
        ]
        self.assertEqual(expected_toolchange_command, weaver.get_toolchange_commands(t0_codes))

    def test_get_toolchange_commands_with_last_used_t0_next_is_none(self):
        t0_codes = GcodeObject([])
        t1_codes = GcodeObject([])
        weaver = DualstrusionWeaver(t0_codes, t1_codes)
        weaver.last_position_0 = 'G1 X50 Y51'
        weaver.next_position_0 = None
        weaver.last_position_1 = 'G1 X100 Y100'
        weaver.next_position_1 = 'G1 X0 Y0 Z400'
        expected_toolchange_command = [
            "M135 T0\n",
            "G1 X50 Y51\n",
        ]
        self.assertEqual(expected_toolchange_command, weaver.get_toolchange_commands(t0_codes))

    def test_get_toolchange_commands_with_last_used_t1_last_is_none(self):
        t0_codes = GcodeObject([])
        t1_codes = GcodeObject([])
        weaver = DualstrusionWeaver(t0_codes, t1_codes)
        weaver.last_position_0 = 'G1 X50 Y50'
        weaver.next_position_0 = 'G1 X0 Y0 Z500'
        weaver.last_position_1 = None
        weaver.next_position_1 = 'G1 X0 Y0 Z400'
        expected_toolchange_command = [
            "M135 T1\n",
        ]
        self.assertEqual(expected_toolchange_command, weaver.get_toolchange_commands(t1_codes))

    def test_get_toolchange_commands_with_last_used_t1_next_is_none(self):
        t0_codes = GcodeObject([])
        t1_codes = GcodeObject([])
        weaver = DualstrusionWeaver(t0_codes, t1_codes)
        weaver.last_position_0 = 'G1 X50 Y50'
        weaver.next_position_0 = 'G1 X0 Y0 Z500'
        weaver.last_position_1 = 'G1 X100 Y100'
        weaver.next_position_1 = None
        expected_toolchange_command = [
            "M135 T1\n",
            "G1 X100 Y100\n",
        ]
        self.assertEqual(expected_toolchange_command, weaver.get_toolchange_commands(t1_codes))
                        
    def test_get_last_location_no_codes(self):
        codes_t0 = [
            "G1 X0 Y0", 
            "G1 X-50 Y-50",
        ]
        codes_t1 = [
            "G1 X0 Y0", 
            "G1 X100 Y100",
        ]
        weaver = DualstrusionWeaver(GcodeObject(codes_t0), GcodeObject(codes_t1))
        weaver.set_last_location(codes_t0[:], weaver.tool_0_codes)
        self.assertEqual(weaver.last_position_0, codes_t0[1])
        self.assertEqual(weaver.last_position_1, None)
        weaver.set_last_location(codes_t1[:], weaver.tool_1_codes)
        self.assertEqual(weaver.last_position_1, codes_t1[1])
        self.assertEqual(weaver.last_position_0, codes_t0[1])

    def test_create_transition_code(self):
        cases = [
            ['G1 X50.05 Y51 Z0', 'G1 X99 Y99 Z100', ['G1 X50.05 Y51 Z100\n']],
            ['G1 Y50 Z0', 'G1 X12 Y13 Z50', ['G1 Y50 Z50\n']],
            ['G1 Z0', 'G1 X12 Y13 Z50', ['G1 Z50\n']],
            ['G1 Z0', 'G1 X12 Y12', []],
            [None, 'G1 Z100', []],
            ['G1 X50 Y51', None, ['G1 X50 Y51\n']],
        ]
        for case in cases:
            self.assertEqual(case[2], DualstrusionWeaver.create_transition_location(case[0], case[1]))


if __name__ == "__main__":
    unittest.main()
