from pdf_to_svg import PdfToSvg
from svg_to_gcode import SvgToGCode
from multi_colour_manager import MultiColorManager

# List of printers
PRINTERS = {
    "A1 Mini": {"max_x": 180, "max_y": 180, "max_z": 180},
    "P1S/P2S": {"max_x": 240, "max_y": 255, "max_z": 255},
    "A1": {"max_x": 255, "max_y": 255, "max_z": 240},
    "H2D": {"max_x": 325, "max_y": 325, "max_z": 320},
}

print("\nWelcome to Ink in 3D Printer")

# Choose printing mode
print("\nSelect printing mode:")
print("  1. Single Colour (no pen swaps)")
print("  2. Multi Colour (with pen swaps)")

while True:
    try:
        mode_choice = int(input("\nSelect mode (1-2): "))
        if mode_choice in (1, 2):
            print_mode = "Single Colour" if mode_choice == 1 else "Multi Colour"
            print(f"✓ Selected: {print_mode}")
            break
        else:
            print("Invalid selection. Please choose 1 or 2.")
    except ValueError:
        print("Invalid input. Please enter a number.")
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
            print(f"\nSelected: {selected_printer}")
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
        print(f"Detail level set to: {line_segments} segments")
        break
    except ValueError:
        print("Invalid input. Please enter a valid number.")

retraction_height = 20   # Height to raise pen when moving (mm)
plot_height = 63         # Initial layer height (mm)
pen_offset_forward = 45  # Forward offset of pen from nozzle (mm)

max_x = printer_config['max_x']
max_y = printer_config['max_y'] - pen_offset_forward

print(f"Usable print area with pen offset: {max_x}x{max_y}mm")

pdf_to_svg = PdfToSvg("sample4.pdf", "drawing.svg", max_x, max_y)

if mode_choice == 1:
    # Single Colour Mode
    width, height, temp_svg, _ = pdf_to_svg.run(split_colors=False)
    
    svg_to_gcode = SvgToGCode(
        svg_file="drawing.svg",
        output_file="output.gcode",
        scale_factor=pdf_to_svg.scale_factor,
        line_segments=line_segments,
        retraction_height=retraction_height,
        plot_height=plot_height,
        max_x=max_x,
        max_y=max_y,
        pen_offset_y=pen_offset_forward
    )
    
    svg_to_gcode.run()
    print("\n✓ Single colour G-code saved to output.gcode")

else:
    # Multi Colour Mode
    width, height, temp_svg, color_svgs = pdf_to_svg.run(split_colors=True)
    
    manager = MultiColorManager(
        color_svgs=color_svgs,
        output_file="final_multicolour.gcode",
        scale_factor=pdf_to_svg.scale_factor,
        line_segments=line_segments,
        retraction_height=retraction_height,
        plot_height=plot_height,
        max_x=max_x,
        max_y=max_y,
        pen_offset_y=pen_offset_forward
    )
    
    manager.assemble()
    print("\n✓ Multi colour G-code saved to final_multicolour.gcode")