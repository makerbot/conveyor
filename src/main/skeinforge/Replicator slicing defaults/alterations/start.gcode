(*** Start Gcode for the Rep2 ***)
(*** MakerWare's gcode parser is rather strict, so only ***)
(*** edit this file if you know what you're doing! ***)
M136 (enable build)
M73 P0
G162 X Y F2000(home XY axes maximum)
G161 Z F900(home Z axis minimum)
G92 X0 Y0 Z-5 A0 B0 (set Z to -5)
G1 Z0.0 F900(move Z to '0')
G161 Z F100(home Z axis minimum)
M132 X Y Z A B (Recall stored home offsets for XYZAB axis)
G92 X163 Y75 Z0 A0 B0
G1 X-112 Y-73 Z150 F3300.0 (move to waiting position)
G130 X20 Y20 A20 B20 (Lower stepper Vrefs while heating)
M135 T0
M104 T0 S230
M133 T0
G130 X127 Y127 A127 B127 (Set Stepper motor Vref to defaults)
(*** End start gcode ***)
