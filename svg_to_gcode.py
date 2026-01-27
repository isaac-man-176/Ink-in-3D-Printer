from svgpathtools import svg2paths
import numpy as np
import re

class SvgToGCode:
    def __init__(self, svg_file, output_file, scale_factor=1.0):
        self.svg_file = svg_file
        self.output_file = output_file
        self.scale_factor = scale_factor

        # Load paths
        self.paths, _ = svg2paths(svg_file)

        # Remove Bounding Boxes
        self.paths = [p for p in self.paths if p.length() > 0.1]

        # NEW: apply SVG <g transform="matrix(...)"> transforms
        self.apply_svg_transforms()

        # Split Compound Paths
        self.split_compound_paths()

        # Scale actual geometry
        self.scale_paths(scale_factor)

        # Normalize once before fitting
        self.normalize_paths()

        # Fit to 255x255 bed
        # self.fit_to_bed(255)

        # Normalize again after fitting
        self.normalize_paths()

        self.gcode = []

    def apply_svg_transforms(self):
        with open(self.svg_file, "r") as f:
            svg = f.read()

        matrices = re.findall(r'transform="matrix\(([^)]+)\)"', svg)
        transforms = []

        for m in matrices:
            # NEW: split on commas or spaces
            nums = re.split(r"[ ,]+", m.strip())
            a, b, c, d, e, f = map(float, nums)
            transforms.append((a, b, c, d, e, f))

        # If number of transforms doesn't match number of paths,
        # apply identity transforms to missing ones
        while len(transforms) < len(self.paths):
            transforms.append((1, 0, 0, 1, 0, 0))

        for path, (a, b, c, d, e, f) in zip(self.paths, transforms):
            for seg in path:
                seg.start = complex(
                    a * seg.start.real + c * seg.start.imag + e,
                    b * seg.start.real + d * seg.start.imag + f
                )
                seg.end = complex(
                    a * seg.end.real + c * seg.end.imag + e,
                    b * seg.end.real + d * seg.end.imag + f
                )
                if hasattr(seg, "control1"):
                    seg.control1 = complex(
                        a * seg.control1.real + c * seg.control1.imag + e,
                        b * seg.control1.real + d * seg.control1.imag + f
                    )
                if hasattr(seg, "control2"):
                    seg.control2 = complex(
                        a * seg.control2.real + c * seg.control2.imag + e,
                        b * seg.control2.real + d * seg.control2.imag + f
                    )


    # ---------------------------------------------------------
    # Scale actual path coordinates
    # ---------------------------------------------------------
    def scale_paths(self, factor):
        for path in self.paths:
            for seg in path:
                seg.start *= factor
                seg.end *= factor
                if hasattr(seg, "control1"):
                    seg.control1 *= factor
                if hasattr(seg, "control2"):
                    seg.control2 *= factor

    # ---------------------------------------------------------
    # Normalize all paths together (preserve relative positions)
    # ---------------------------------------------------------
    def normalize_paths(self):
        xs = []
        ys = []

        for path in self.paths:
            for seg in path:
                xs.extend([seg.start.real, seg.end.real])
                ys.extend([seg.start.imag, seg.end.imag])

        min_x = min(xs)
        min_y = min(ys)

        offset = complex(-min_x, -min_y)

        for path in self.paths:
            for seg in path:
                seg.start += offset
                seg.end += offset
                if hasattr(seg, "control1"):
                    seg.control1 += offset
                if hasattr(seg, "control2"):
                    seg.control2 += offset

    # ---------------------------------------------------------
    # Fit drawing inside 255x255 bed
    # ---------------------------------------------------------
    def fit_to_bed(self, bed_size=255):
        xs = []
        ys = []

        for path in self.paths:
            for seg in path:
                xs.extend([seg.start.real, seg.end.real])
                ys.extend([seg.start.imag, seg.end.imag])

        width = max(xs)
        height = max(ys)

        scale = bed_size / max(width, height)

        for path in self.paths:
            for seg in path:
                seg.start *= scale
                seg.end *= scale
                if hasattr(seg, "control1"):
                    seg.control1 *= scale
                if hasattr(seg, "control2"):
                    seg.control2 *= scale

    # ---------------------------------------------------------
    # Helper to add G-code lines
    # ---------------------------------------------------------
    def add(self, line):
        self.gcode.append(line)

    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------
    def add_header(self):
        self.add("; ------------Initial Sequence------------")
        self.add("G28             ;Home all axes")
        self.add("G92 E0          ;Reset extruder")
        self.add("M82             ;Absolute extrusion coordinates")
        self.add("G90             ;Absolute position coordinates")
        self.add("G1 X0 Y255 Z0 ")
        self.add("G1 X0.01 Y254.99 Z0 E0.00001 F1200")
        self.add("G1 Z5 ; pen up")
        self.add("; ------------Initial Sequence------------")

    # ---------------------------------------------------------
    # Footer
    # ---------------------------------------------------------
    def add_footer(self):
        self.add("; ------------End Sequence------------")
        self.add("M84            ;Disable Motors")
        self.add("; ------------End Sequence------------")

    # ---------------------------------------------------------
    # Boundary square
    # ---------------------------------------------------------
    def draw_boundry(self):
        self.add("G0 X0 Y0")
        self.add("G1 Z0 ; pen down")
        self.add("G0 X0 Y255 Z0")
        self.add("G0 X255 Y255 Z0")
        self.add("G0 X255 Y0 Z0")
        self.add("G0 X0 Y0 Z0")
        self.add("G1 Z50 ; pen up")

    # ---------------------------------------------------------
    # Convert paths to G-code
    # ---------------------------------------------------------
    def convert_paths(self):
        for path in self.paths:
            first = True

            for segment in path:
                for i, t in enumerate(np.linspace(0, 1, 50)):
                    point = segment.point(t)
                    x, y = point.real, point.imag

                    if first and i == 0:
                        self.add(f"G1 X{x:.3f} Y{y:.3f} F3000")
                        self.add("G1 Z0 ; pen down")
                        first = False
                    else:
                        self.add(f"G1 X{x:.3f} Y{y:.3f} F2000")

            self.add("G1 Z50 ; pen up")

    # ---------------------------------------------------------
    # Split Compound Paths
    # ---------------------------------------------------------
    def split_compound_paths(self):
        new_paths = []
        for path in self.paths:
            # svgpathtools stores subpaths as separate segments
            # but they share the same Path object
            subpaths = path.continuous_subpaths()
            for sp in subpaths:
                new_paths.append(sp)
        self.paths = new_paths

    # ---------------------------------------------------------
    # Save G-code
    # ---------------------------------------------------------
    def save(self):
        with open(self.output_file, "w") as f:
            f.write("\n".join(self.gcode))

    # ---------------------------------------------------------
    # Run
    # ---------------------------------------------------------
    def run(self, drawBoundry=False):
        self.add_header()
        if drawBoundry:
            self.draw_boundry()
        self.convert_paths()
        self.add_footer()
        self.save()
