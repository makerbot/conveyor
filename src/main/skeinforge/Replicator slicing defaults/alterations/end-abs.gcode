(*** End Gcode for the Rep2 ***)
(*** MakerWare's gcode parser is strict. Do not edit ***)
(*** this file unless you know what you're doing! ***)

(*** Code that follows a ";" or "(" is considered a comment, ***)
(*** and will not be evaluated by the Gcode Line Parser. ***)
 
M18 A B (Turn off A and B Steppers)
G1 Z155 F900 (Move the platform to the bottom of the machine)
G162 X Y F2000 (Send the gantry to its home position)
M18 X Y Z (Turn off steppers after a build)

(*** To cool additional tools such as the left extruder or heated platform, ***)
(*** remove the ";" from the applicable line ***)
M104 S0 T0 (Turn the right extruder heater off)
;M104 S0 T1 (Turn the left extruder heater off)
M109 S0 T0 (Turn the platform heater off)

M70 P5 (We <3 Making Things!)
M72 P1  ( Play Ta-Da song )
M73 P100 (Set the build percent to 100)
M137 (build end notification)
(*** End end gcode ***)
