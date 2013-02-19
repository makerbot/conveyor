(*** Start Gcode for the Rep2x ***)
(*** MakerWare's gcode parser is strict. Do not edit ***)
(*** this file unless you know what you're doing! ***)

(*** Code that follows a ";" or "(" is considered a comment, ***)
(*** and will not be evaluated by the Gcode Line Parser. ***)
 
M136 (enable build)
M73 P0 (Set initial build percentage)
G162 X Y F2000 (home to XY axes maximum)
G161 Z F900 (home to Z axis minimum)
G92 X0 Y0 Z-5 A0 B0 (set Z to -5)
G1 Z0.0 F900 (set Z to '0')
G161 Z F100 (home to Z axis minimum)
M132 X Y Z A B (Recall stored home offsets for XYZAB axis)

(*** Set the homing position ***)
G92 X152 Y72 Z0 A0 B0 (Replicator Home Position)

G1 X-112 Y-73 Z150 F3300.0 (Waiting Position)
G130 X20 Y20 A20 B20 (Lower stepper Vrefs while heating)

(*** These lines set the primary extruder. On a single-extruder bot, this ***)
(*** will always be the right extruder. On a dual-extruder bot it will be  ***)
(*** the extruder you are printing with. Comment out the extruder not being ***)
(*** used as the primary extruder. ***)
M135 T0 (Set the Right extruder as the main Extruder)
;M135 T1 (Set the Left extruder as the main Extruder)

(*** To disable a heated build platform, add a ";" at the beginning of these lines ***)
M109 T0 S110 (Set the platform temp to 110C)
M134 T0 (Wait for the Platform to Heat Up)

(*** To heat a tool, make sure the applicable line is not preceded by a ";" ***)
(*** Lines for tools not being used must be preceded by a ";"  ***)
M104 T0 S230 (Set the right extruder temp to 230C)
;M104 T1 S230 (Set the left extruder temp to 230C)

(*** These codes are used to wait for a specific tool to heat up.***)
(*** Lines for tools in use should not be preceded by a ";" ***)
(*** Lines for tools not in use should be preceded by a ";" ***)
M133 T0 (Wait for Right Extruder to Heat Up)
;M133 T1 (Wait for Left Extruder to Heat Up)

G130 X127 Y127 A127 B127 (Set Stepper motor Vref to defaults)
(*** End start gcode ***)
