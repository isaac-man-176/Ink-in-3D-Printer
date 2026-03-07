# multi_color_manager.py
import os
from svg_to_gcode import SvgToGCode

class MultiColorManager:
    """
    Handles multi‑colour printing:
    - receives a dict of {color_hex: svg_path}
    - asks user for dock position for each colour (0 = skip)
    - runs each SVG through SvgToGCode
    - merges colours by dock position
    - wraps each dock group with pickup/dropoff comments
    - header/footer appear only once
    """

    def __init__(self, color_svgs, output_file, scale_factor, line_segments,
                 retraction_height, plot_height, max_x, max_y, pen_offset_y):

        # If no colours detected but paths exist, default to black
        if not color_svgs:
            print("No colours detected. Defaulting to black (#000000).")
            # The caller always passes the base SVG as the only file
            # so we treat the entire drawing as black
            # Expecting the caller to pass a dict like {} when no colours exist
            raise ValueError("PdfToSvg returned no colour layers. Cannot continue.")

        self.color_svgs = color_svgs
        self.output_file = output_file
        self.scale_factor = scale_factor
        self.line_segments = line_segments
        self.retraction_height = retraction_height
        self.plot_height = plot_height
        self.max_x = max_x
        self.max_y = max_y
        self.pen_offset_y = pen_offset_y

        self.dock_positions = {}   # {color_hex: dock_number}

    # -------------------------------------------------------------
    # Pen pickup/dropoff sequences (X value is parameterized)
    def get_pickup_sequence(self, x_pos):
        return [
            "G1 Z82 F2000",
            f"G1 X{x_pos}",
            "G1 Z38",
            "G1 Y0",
            "G1 Z89.5 F1000",
            "G1 Z88",
            "G1 Y20 F300",
            "G1 Y60 F2000"
        ]

    def get_dropoff_sequence(self, x_pos):
        return [
            "G1 Z83 F2000",
            f"G1 X{x_pos}",
            "G1 Z88 F1500",
            "G1 Y20",
            "G1 Y0 F1000",
            "G1 Z70 F400",
            "G1 Z38 F600",
            "G1 Y60 F2000",
            "G1 Z83"
        ]

    def get_docker_x_position(self, docker_num):
        """Calculate X position for docker based on docker number (1-6)"""
        return 16 + (docker_num - 1) * 45

    # Ask user for dock position for each colour (0 = skip)
    def ask_dock_positions(self):
        print("\nDetected colours:")
        for color_hex in self.color_svgs.keys():
            print(f"  • #{color_hex}")

        print("\nAssign a dock position (1–6) for each colour.")
        print("Enter 0 to skip this colour entirely.\n")

        for color_hex in self.color_svgs.keys():
            while True:
                pos = input(f"Dock position for colour #{color_hex}: ").strip()
                if pos in ("0", "1", "2", "3", "4", "5", "6"):
                    self.dock_positions[color_hex] = int(pos)
                    break
                print("Invalid. Enter a number 0–6.")

    # -------------------------------------------------------------
    # Extract header/footer from one G-code file
    # -------------------------------------------------------------
    def _extract_header_footer(self, lines):
        header = []
        footer = []
        body = []

        in_header = True
        in_footer = False

        for line in lines:
            if "Initial Sequence" in line:
                header.append(line)
                continue
            if "End Sequence" in line:
                in_footer = True
                footer.append(line)
                continue

            if in_header:
                header.append(line)
                if "; pen up" in line:
                    in_header = False
                continue

            if in_footer:
                footer.append(line)
                continue

            body.append(line)

        return header, body, footer

    # -------------------------------------------------------------
    # Convert each colour SVG → cleaned G‑code block
    # -------------------------------------------------------------
    def _convert_each_colour(self):
        blocks = {}
        header = None
        footer = None

        for color_hex, svg_path in self.color_svgs.items():
            temp_gcode = f"{svg_path}.gcode"

            converter = SvgToGCode(
                svg_file=svg_path,
                output_file=temp_gcode,
                scale_factor=self.scale_factor,
                line_segments=self.line_segments,
                retraction_height=self.retraction_height,
                plot_height=self.plot_height,
                max_x=self.max_x,
                max_y=self.max_y,
                pen_offset_y=self.pen_offset_y
            )

            converter.run()

            with open(temp_gcode, "r") as f:
                lines = f.read().splitlines()

            if header is None:
                header, body, footer = self._extract_header_footer(lines)
            else:
                _, body, _ = self._extract_header_footer(lines)

            # If body is empty → no paths found
            if not body:
                raise ValueError(f"No paths found for colour #{color_hex}. Cannot continue.")

            blocks[color_hex] = body

        return header, blocks, footer

    # -------------------------------------------------------------
    # Assemble final G‑code
    # -------------------------------------------------------------
    def assemble(self):
        self.ask_dock_positions()

        header, blocks, footer = self._convert_each_colour()

        # Group colours by dock position, skipping dock=0
        dock_groups = {}
        for color_hex, dock in self.dock_positions.items():
            if dock == 0:
                print(f"Skipping colour #{color_hex} (dock 0).")
                continue
            dock_groups.setdefault(dock, []).append(color_hex)

        final = []
        final.extend(header)

        # Process each dock group
        for dock, colours in dock_groups.items():
            final.append(f"; Pick up pens at dock {dock} for colours: " +
                         ", ".join(f"#{c}" for c in colours))
            x_pos = self.get_docker_x_position(dock)
            final.extend(self.get_pickup_sequence(x_pos))

            for c in colours:
                final.append(f"; Drawing colour #{c}")
                final.extend(blocks[c])

            final.append(f"; Drop off pens at dock {dock}")
            final.extend(self.get_dropoff_sequence(x_pos))

        final.extend(footer)

        with open(self.output_file, "w") as f:
            f.write("\n".join(final))

        print(f"\nSaved multicolour G‑code to {self.output_file}")
