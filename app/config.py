# List of printers
PRINTERS = {
    "A1 Mini": {"max_x": 180, "max_y": 180, "max_z": 180},
    "P1S/P2S": {"max_x": 240, "max_y": 255, "max_z": 255},
    "A1": {"max_x": 255, "max_y": 255, "max_z": 240},
    "H2D": {"max_x": 325, "max_y": 325, "max_z": 320},
}

# Height to raise pen when moving and to not plot (mm)
RETRACT_HEIGHT = 20

# Height of pen when plotting
PLOT_HEIGHT = 63

# Forward offset of pen so that center of pen is the coords instead of extruder
PEN_OFFSET_FWD = 45