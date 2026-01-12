# this program converts svg to g-code

# SVG → paths → segments → math → points → G‑code

# libraries needed
from svgpathtools import svg2paths # to read SVG, extract curves, translate to points
import numpy as np

# input file converted into paths
paths, attributes = svg2paths("drawing.svg")

gcode = []

# helper function to simplify adding more g-code to array
def add(line): 
    gcode.append(line) 

user_input = input("Draw boundry square? Enter Y/N:")

# Gcode for Bambu lab header  
add("; ------------Initial Sequence------------") 
add("G28             ;Home all axes") 
add("G92 E0          ;Reset extruder") 
add("M82             ;Absolute extrusion coordinates")
add("G90             ;Absolute position coordinates")
add("M710 A1 S255    ;Turn on MC fan to full speed")

add("G1 X0 Y255 Z0 ")
add("G1 X0.01 Y254.99 Z0 E0.0000001 F1200")
add("G1 Z5 ; pen up")
add("; ------------Initial Sequence------------")

if user_input == "Y" or user_input == "y":
    # Gcode for Rectangle Check - draws square boundary (printer can print inside this boundry)
    add("G0 X0 Y0")
    add("G1 Z0 ; pen down")
    add("G0 X0 Y255 Z0")
    add("G0 X255 Y255 Z0")
    add("G0 X255 Y0 Z0")
    add("G0 X0 Y0 Z0")
    add("G1 Z5 ; pen up")

for path in paths: # for every stroke
    first = True

    for segment in path: # for every curve
        for i, t in enumerate(np.linspace(0, 1, 50)): # split every curve into 50 straight line segments
            point = segment.point(t)
            x, y = point.real, point.imag

            if first and i == 0: # sees if pen is retracted and then unretracts if neccessary
                add(f"G1 X{x:.3f} Y{y:.3f} F3000") 
                add("G1 Z0 ; pen down")
                first = False
            else:
                add(f"G1 X{x:.3f} Y{y:.3f} F2000") # adds g-code for every point

    add("G1 Z5 ; pen up") # retracts pen after finished every path

# Gcode for Bambu lab end of file
add("; ------------End Sequence------------") 
add("M710 A1 S0     ;Turn off MC fan")
add("M84            ;Disable Motors")
add("; ------------End Sequence------------") 

# outputting gcode to output.gcode
with open("output.gcode", "w") as f: 
    f.write("\n".join(gcode))