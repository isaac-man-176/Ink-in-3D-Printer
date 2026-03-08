# This file is for testing backend directly without frontend

from app.pipeline.pdf_to_svg import PdfToSvg
from app.pipeline.svg_to_gcode import SvgToGCode
from app.pipeline.multi_colour_manager import MulticolourManager
from app.config import PRINTERS, PEN_OFFSET_FWD, RETRACT_HEIGHT, PLOT_HEIGHT

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

max_x = printer_config['max_x']
max_y = printer_config['max_y'] - PEN_OFFSET_FWD

print(f"Usable print area with pen offset: {max_x}x{max_y}mm")

pdf_to_svg = PdfToSvg("_samples/sample4.pdf", "drawing.svg", max_x, max_y)

if mode_choice == 1:
    # Single Colour Mode
    width, height, temp_svg, _ = pdf_to_svg.run(split_colours=False)
    
    svg_to_gcode = SvgToGCode(
        svg_file="drawing.svg",
        output_file="output.gcode",
        scale_factor=pdf_to_svg.scale_factor,
        line_segments=line_segments,
        retraction_height=RETRACT_HEIGHT,
        plot_height=PLOT_HEIGHT,
        max_x=max_x,
        max_y=max_y,
        pen_offset_y=PEN_OFFSET_FWD
    )
    
    svg_to_gcode.run()
    print("\n✓ Single colour G-code saved to output.gcode")

else:
    # Multi Colour Mode
    width, height, temp_svg, colour_svgs = pdf_to_svg.run(split_colours=True)
    
    manager = MulticolourManager(
        colour_svgs=colour_svgs,
        output_file="final_multicolour.gcode",
        scale_factor=pdf_to_svg.scale_factor,
        line_segments=line_segments,
        retraction_height=RETRACT_HEIGHT,
        plot_height=PLOT_HEIGHT,
        max_x=max_x,
        max_y=max_y,
        pen_offset_y=PEN_OFFSET_FWD
    )
    
    manager.assemble()
    print("\n✓ Multi colour G-code saved to final_multicolour.gcode")