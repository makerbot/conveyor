import re
import mock
import unittest

class DualstrusionWeaver(object):

    def __init__(self, tool_0_codes, tool_1_codes):
        self.tool_0_codes = tool_0_codes
        self.tool_1_codes = tool_1_codes
        self.last_used_codes = self.tool_0_codes
        self.new_codes = []

    def combine_codes(self):
        while len(self.tool_0_codes.gcodes) is not 0 and len(self.tool_1_codes.gcodes) is not 0:
            next_gcode_obj = self.get_next_code_list()
            next_layer = self.get_next_layer(next_gcode_obj)
            self.new_codes.extend(next_layer)
        if len(self.tool_0_codes.gcodes) is not 0:
            self.new_codes.extend(self.tool_0_codes.gcodes)
        elif len(self.tool_1_codes.gcodes) is not 0:
            self.new_codes.extend(self.tool_1_codes.gcodes)
        return self.new_codes

    def get_next_code_list(self):
        tool_0_height = self.tool_0_codes.peek_next_layer_height()
        tool_1_height = self.tool_1_codes.peek_next_layer_height()
        if tool_0_height < tool_1_height or len(self.tool_1_codes.gcodes) == 0:
            self.last_used_codes = self.tool_0_codes
        elif tool_1_height < tool_0_height or len(self.tool_0_codes.gcodes) == 0:
            self.last_used_codes = self.tool_1_codes
        return self.last_used_codes

    def get_next_layer(self, gcode_obj):
        return gcode_obj.get_next_layer()

class TestDualstrusionWeaver(unittest.TestCase):

    def test_combine_codes(self):
        t0_codes = [
            "<layer>",
            "M132",
            "G92 X0 Y0 Z0 A0 B0",
            "G1 X50 Y50 Z0.5",
            "</layer>",
            "<layer>",
            "M132",
            "G1 X0 Y0 Z1.5",
            "G92 X99 Y99:",
            "</layer>",
        ]
        t1_codes = [
            "G1 X1 Y2 Z0.5",
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
            "<layer>",
            "M132",
            "G92 X0 Y0 Z0 A0 B0",
            "G1 X50 Y50 Z0.5",
            "</layer>",
            "G1 X1 Y2 Z0.5",
            "G1 X59 Y58",
            "M132",
            "G92",
            "(Slice 54, 3 Extruder)",
            "G1 X1 Y2 Z1.5",
            "G99",
            "M101",
            "M105",
            "(Slice 55, 3 Extruder)",
            "<layer>",
            "M132",
            "G1 X0 Y0 Z1.5",
            "G92 X99 Y99:",
            "</layer>",
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
            "</layer>",
            "<layer>",
            "M132",
            "G1 X0 Y0 Z0",
            "G92 X99 Y99:",
            "</layer>",
            ]
        expected_t0_codes = t0_codes[:5]
        expected_leftovers = t0_codes[5:]
        tool_0_codes = GcodeObject(gcodes=t0_codes[:])
        tool_1_codes = GcodeObject(gcodes=[])
        weaver = DualstrusionWeaver(tool_0_codes, tool_1_codes)
        self.assertEqual(expected_t0_codes, weaver.get_next_layer(tool_0_codes))
        self.assertEqual(expected_leftovers, tool_0_codes.gcodes)

    def test_get_next_code_list_equal_height(self):
        codes = [
            "<layer>",
            "G1 Z.5",
            "</layer>",
            "<layer>",
            "G1 Z1.5",
            "</layer>",
            "<layer>",
            "G1 Z2.5",
            "</layer>",
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

class GcodeObject(object):

    def __init__(self, gcodes=[]):
        self.gcodes = gcodes
        self.skeinforge_tag = re.compile("</layer>")
        self.miraclegrue_tag = re.compile("\(Slice (\d+), (\d+) Extruder\)")
        self.layer_height_regex = re.compile("[gG]1.*?[zZ](0?\.?[\d]+)")
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
            if re.match(self.skeinforge_tag, code) or re.match(self.miraclegrue_tag, code):
                break
        return self.last_layer_height

    def get_next_layer(self):
        layer = []
        for line in self.gcodes:
            layer.append(line)
            if re.match(self.skeinforge_tag, line) or re.match(self.miraclegrue_tag, line):
                break
        for line in layer:
            self.gcodes.remove(line)
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
            "G1 X0 Y0 Z0.5",
            "G1 X0 Y0 Z1",
            "G1 X0 Y0 Z20",
        ]
        self.gcode_obj.gcodes = gcodes
        expected_next = .5
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
        self.gcode_obj.gcodes = gcodes
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
        self.gcode_obj.gcodes = gcodes
        expected_next = .5
        self.assertEqual(expected_next, self.gcode_obj.peek_next_layer_height())

    def test_peek_next_layer_height_no_layer_height(self):
        gcodes = [
            "M134 T0",
            "G92 X0 Y0 Z0",
            "G1 X0 Y0 A0",
            "M99",
        ]
        self.gcode_obj.gcodes = gcodes
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
        self.gcode_obj.gcodes = gcodes[:]
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
            "</layer>",
            "<layer>",
            "G1 X1 Y2 Z3",
            "G92 X100 Y100 Z100 A100",
            "</layer>",
        ]
        self.gcode_obj.gcodes = gcodes[:]
        expected_layer = [
            "M134 T0",
            "G1 X0 Y0 Z0",
            "G92 X0 Y0 Z50",
            "M99",
            "(some interesting comments)",
            "</layer>"
        ]
        expected_leftovers = gcodes[6:]
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
        self.gcode_obj.gcodes = gcodes[:]
        expected_layer = [
            "M134 T0",
            "G1 X0 Y0 Z0",
            "G92 X0 Y0 Z50",
            "M99",
            "(some interesting comments)",
            "(Slice 54, 3 Extruder)",
        ]
        expected_leftovers = gcodes[6:]
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
        self.gcode_obj.gcodes = gcodes[:]
        expected_layer = [
            "M134 T0",
            "G1 X0 Y0 Z0",
            "G92 X0 Y0 Z50",
            "M99",
            "(some interesting comments)",
            "G1 X1 Y2 Z3",
            "G92 X100 Y100 Z100 A100",
        ]
        expected_leftovers = []
        self.assertEqual(expected_layer, self.gcode_obj.get_next_layer())
        self.assertEqual(len(self.gcode_obj.gcodes), len(expected_layer) - len(gcodes))
        self.assertEqual(expected_leftovers, self.gcode_obj.gcodes)

if __name__ == "__main__":
    unittest.main()
