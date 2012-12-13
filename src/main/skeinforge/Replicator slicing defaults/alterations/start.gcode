(*** Start Gcode for the Rep2 ***)
(*** MakerWare's gcode parser is rather strict, so only ***)
(*** edit this file if you know what you're doing! ***)

(*** Note about comments: code that follows a ";" or "(" is considered ***)
(*** a comment, and will not be evaluated by the Gcode Line Parser. ***)
 
M136 (enable build)
M73 P0 (Set initial build percentage)
G162 X Y F2000 (home XY axes maximum)
G161 Z F900 (home Z axis minimum)
G92 X0 Y0 Z-5 A0 B0 (set Z to -5)
G1 Z0.0 F900 (move Z to '0')
G161 Z F100 (home Z axis minimum)
M132 X Y Z A B (Recall stored home offsets for XYZAB axis)

(*** Set the homing position for either the Rep1 or Rep2. ***)
(*** Remove the ";" from the applicable line to print with a specific machine. ***)
(*** Make sure the unused machine's line is preceeded by a ";" ***)
G92 X163 Y75 Z0 A0 B0 (Rep2 Home Position)
;G92 X152 Y75 Z0 A0 B0 (Rep1 Home Position)

G1 X-112 Y-73 Z150 F3300.0 (Waiting Position)
G130 X20 Y20 A20 B20 (Lower stepper Vrefs while heating)

M135 T0 (Set the Right extruder as the main Extruder)
M135 T1 (Set the Left extruder as the main Extruder)

(*** To heat additional tools such as the left extruder or heated platform, ***)
(*** remove the ";" from the applicable line ***)
M104 T0 S230 (Set the right extruder temp to 230C)
;M104 T1 S230 (Set the left extruder temp to 230C)
;M109 T0 110 (Set the platform temp to 110C)

(*** These codes are used to wait for a specific tool to heat up.***)
(*** Remove the ";" from any applicable line, and comment ***)
(*** out any unapplicable lines ***)
M133 T0 (Wait for Right Extruder to Heat Up)
;M133 T1 (Wait for Left Extruder to Heat Up)
;M134 T0 (Wait for the Platform to Heat Up)

G130 X127 Y127 A127 B127 (Set Stepper motor Vref to defaults)
(*** End start gcode ***)
