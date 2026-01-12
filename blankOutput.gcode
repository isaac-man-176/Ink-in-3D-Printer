; ------------Initial Sequence------------
G28             ;Home all axes
G92 E0          ;Reset extruder
M82             ;Absolute extrusion coordinates
G90             ;Absolute position coordinates
M710 A1 S255    ;Turn on MC fan to full speed
G1 X0 Y255 Z0 
G1 X0.01 Y254.99 Z0 E0.0000001 F1200
; ------------Initial Sequence------------
G28
G0 X0 Y0 Z0
G0 X0 Y255 Z0
G0 X255 Y255 Z0
G0 X255 Y0 Z0
G0 X0 Y0 Z0
; ------------End Sequence------------
G28            ;Home
M710 A1 S0     ;Turn off MC fan
M84            ;Disable Motors
; ------------End Sequence------------