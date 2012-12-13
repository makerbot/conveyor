(*** End Gcode for the Rep2 ***)
(*** MakerWare's gcode parser is rather strict, so only ***)
(*** edit this file if you know what you're doing! ***)

(*** Note about comments: code that follows a ";" or "(" is considered ***)
(*** a comment, and will not be evaluated by the Gcode Line Parser. ***)
 
M18 A B(Turn off A and B Steppers)
G1 Z155 F900 (Move the platform to the bottom of the machine)
G162 X Y F2000 (Home the gantry to its home position)
M18 X Y Z(Turn off steppers after a build)

(*** To cool additional tools such as the left extruder or heated platform, ***)
(*** remove the ";" from the applicable line ***)
M104 S0 T0 (Set the right extruder temp to 0C)
;M104 S0 T1 (Set the left extruder temp to 0C)
;M109 S0 T0 (Set the platform temp to 0C)

M70 P5 (We <3 Making Things!)
M72 P1  ( Play Ta-Da song )
M73 P100 (Set the build percent to 100)
M137 (build end notification)
(*** End end gcode ***)
