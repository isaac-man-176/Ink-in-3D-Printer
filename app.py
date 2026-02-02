# app.py
from svg_to_gcode import SvgToGCode
from pdf_to_svg import PdfToSvg

# List of printers
PRINTERS = {
    "A1 Mini": {"max_x": 180, "max_y": 180, "max_z": 180},
    "P1S/P2S": {"max_x": 255, "max_y": 255, "max_z": 255},
    "A1": {"max_x": 255, "max_y": 255, "max_z": 240},
    "H2D": {"max_x": 325, "max_y": 325, "max_z": 320},
}

# Pre-conversion user prompts: Asks user which printer they have and how detailed the gcode should be
print("\nWelcome to Ink in 3D Printer")
print("\nPlease select one of the available printers:")
printer_list = list(PRINTERS.keys())
for i, printer in enumerate(printer_list, 1):
    build_vol = PRINTERS[printer]
    print(f"  {i}. {printer} (Build volume: {build_vol['max_x']}x{build_vol['max_y']}x{build_vol['max_z']}mm)")

while True:
    try:
        choice = int(input("\nSelect printer (1-4): "))
        if 1 <= choice <= len(printer_list):
            selected_printer = printer_list[choice - 1]
            printer_config = PRINTERS[selected_printer]
            print(f"\n✓ Selected: {selected_printer}")
            print(f"  Build volume: {printer_config['max_x']}x{printer_config['max_y']}x{printer_config['max_z']}mm")
            break
        else:
            print("Invalid selection. Please choose 1-4.")
    except ValueError:
        print("Invalid input. Please enter a number.")

while True:
    try:
        detail_level = input("\nEnter line segment detail level (default 50): ").strip()
        if detail_level == "":
            line_segments = 50
        else:
            line_segments = int(detail_level)
            if line_segments < 1:
                print("Detail level must be at least 1.")
                continue
        print(f"✓ Detail level set to: {line_segments} segments")
        break
    except ValueError:
        print("Invalid input. Please enter a valid number.")

# More specific parameters (user does not change on use)
retraction_height = 10  # Height to raise pen when moving (mm)
plot_height = 0.2       # Initial layer height (mm)

# conversion pipeline
pdf_to_svg = PdfToSvg("sample4.pdf", "drawing.svg", 255)
pdf_to_svg.run()

# pass the scale factor into SvgToGCode
svg_to_gcode = SvgToGCode("drawing.svg", "output.gcode", scale_factor=pdf_to_svg.scale_factor, line_segments=line_segments, retraction_height=retraction_height, plot_height=plot_height)
svg_to_gcode.run()
