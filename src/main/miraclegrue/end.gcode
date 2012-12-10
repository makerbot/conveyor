(*** End Gcode for the Rep2 ***)
(*** MakerWare's gcode parser is rather strict, so only ***)
(*** edit this file if you know what you're doing! ***)
M18 A B(Turn off A and B Steppers)
G1 Z155 F900
G162 X Y F2000
M18 X Y Z(Turn off steppers after a build)
M104 S0 T0
M70 P5 (We <3 Making Things!)
M72 P1  ( Play Ta-Da song )
M73 P100
M137 (build end notification)
(*** End end gcode ***)
