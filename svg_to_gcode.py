# svg_to_gcode.py
from svgpathtools import svg2paths2
import xml.etree.ElementTree as ET
import numpy as np
import re

class SvgToGCode:
    def __init__(self, svg_file, output_file, scale_factor=1.0, line_segments=50, retraction_height=50, plot_height=0.2):
        self.svg_file = svg_file
        self.output_file = output_file
        self.scale_factor = scale_factor
        self.line_segments = line_segments
        self.retraction_height = retraction_height
        self.plot_height = plot_height

        # Load paths
        self.paths, self.attributes, self.svg_attributes = svg2paths2(self.svg_file)
        print("Loaded paths:", len(self.paths))

        # Apply SVG transforms
        self.apply_svg_transforms()

        # Split Compound Paths
        # self.split_compound_paths()

        # Remove duplicates
        self.dedupe_paths()

        # Sort paths to minimize printer head travel distance
        self.sort_paths()

        # Normalize first
        self.normalize_paths()

        # Scale actual geometry
        self.scale_paths(scale_factor)

        self.gcode = []

    # Transform svg paths so they match svg
    def apply_svg_transforms(self):
        tree = ET.parse(self.svg_file)
        root = tree.getroot()

        # Collect transforms in order of actual <path> elements
        path_transforms = []

        def get_group_transform(elem):
            t = ""
            parent = elem
            while parent is not None:
                tr = parent.get("transform")
                if tr:
                    t = tr + " " + t
                parent = parent.getparent() if hasattr(parent, "getparent") else None
            return t.strip()

        # Extract transforms in correct order
        for elem in root.iter():
            if elem.tag.endswith("path"):
                combined = get_group_transform(elem)
                path_transforms.append(combined)

        # Apply transforms
        new_paths = []
        for i, path in enumerate(self.paths):
            transform_str = path_transforms[i] if i < len(path_transforms) else None

            if transform_str and "matrix" in transform_str:
                nums = re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", transform_str)
                if len(nums) == 6:
                    a, b, c, d, e, f = map(float, nums)
                    for seg in path:
                        seg.start = complex(a*seg.start.real + c*seg.start.imag + e,
                                            b*seg.start.real + d*seg.start.imag + f)
                        seg.end = complex(a*seg.end.real + c*seg.end.imag + e,
                                        b*seg.end.real + d*seg.end.imag + f)
                        if hasattr(seg, "control1"):
                            seg.control1 = complex(a*seg.control1.real + c*seg.control1.imag + e,
                                                b*seg.control1.real + d*seg.control1.imag + f)
                        if hasattr(seg, "control2"):
                            seg.control2 = complex(a*seg.control2.real + c*seg.control2.imag + e,
                                                b*seg.control2.real + d*seg.control2.imag + f)

            new_paths.append(path)

        self.paths = new_paths


    # scale paths
    def scale_paths(self, factor):
        for path in self.paths:
            for seg in path:
                seg.start *= factor
                seg.end *= factor
                if hasattr(seg, "control1"):
                    seg.control1 *= factor
                if hasattr(seg, "control2"):
                    seg.control2 *= factor

    # Normalize paths so it starts at 0,0
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

    # Simple function to add 1 line of gcode
    def add(self, line):
        self.gcode.append(line)

    # Header for all gcodes
    def add_header(self):
        self.add("; ------------Initial Sequence------------")
        self.add("G28             ;Home all axes")
        self.add("G92 E0          ;Reset extruder")
        self.add("M82             ;Absolute extrusion coordinates")
        self.add("G90             ;Absolute position coordinates")
        self.add("G1 X0 Y255 Z0 ")
        self.add("G1 X0.01 Y254.99 Z0 E0.00001 F1200")
        self.add(f"G1 Z{self.retraction_height} ; pen up")
        self.add("; ------------Initial Sequence------------")

    # Footer for all gcodes
    def add_footer(self):
        self.add("; ------------End Sequence------------")
        self.add("M84            ;Disable Motors")
        self.add("; ------------End Sequence------------")

    # Get starting point of a path
    def _get_path_start(self, path):
        return path[0].start if len(path) > 0 else complex(0, 0)

    # Convert paths to gcode with raster-scan ordering (top-to-bottom, left-right alternating)
    def convert_paths(self):
        # Create list of (index, start_point) for all paths
        path_starts = [(i, self._get_centroid(path)) for i, path in enumerate(self.paths)]
        
        # Sort by Y (descending for top-to-bottom), then group by Y-coordinate
        path_starts.sort(key=lambda x: -x[1].imag)  # Top to bottom
        
        # Group paths by Y coordinate with tolerance
        y_threshold = 5  # Group paths within 5 units vertically
        groups = []
        current_group = []
        last_y = None
        
        for idx, start in path_starts:
            if last_y is None or abs(start.imag - last_y) <= y_threshold:
                current_group.append((idx, start))
                last_y = start.imag
            else:
                if current_group:
                    groups.append(current_group)
                current_group = [(idx, start)]
                last_y = start.imag
        
        if current_group:
            groups.append(current_group)
        
        # Process groups in raster pattern: left-right, right-left, repeat
        all_indices = []
        for group_idx, group in enumerate(groups):
            if group_idx % 2 == 0:
                # Left to right
                group.sort(key=lambda x: x[1].real)
            else:
                # Right to left
                group.sort(key=lambda x: -x[1].real)
            
            all_indices.extend([idx for idx, _ in group])
        
        # Draw paths in raster order
        current_pos = complex(0, 0)
        
        for path_idx in all_indices:
            path = self.paths[path_idx]
            first = True
            
            for segment in path:
                for i, t in enumerate(np.linspace(0, 1, self.line_segments)):
                    point = segment.point(t)
                    x, y = point.real, point.imag
                    
                    if first and i == 0:
                        # Move to start of path and lower pen
                        self.add(f"G1 X{x:.3f} Y{y:.3f} F3000")
                        self.add("G1 Z0 ; pen down")
                        first = False
                    else:
                        self.add(f"G1 X{x:.3f} Y{y:.3f} F2000")
            
            # Update current position to end of path
            last_segment = path[-1]
            current_pos = last_segment.end
            
            # Retract pen
            self.add(f"G1 Z{self.retraction_height} ; pen up")

    # Sort paths
    def sort_paths(self):
        def centroid(path):
            xs = []
            ys = []
            for seg in path:
                xs.extend([seg.start.real, seg.end.real])
                ys.extend([seg.start.imag, seg.end.imag])
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
            return (cy, cx)  # sort top→bottom, then left→right

        self.paths.sort(key=centroid)

    # gets the middle of the path the aid with sorting
    def _get_centroid(self, path):
        xs = []
        ys = []
        for seg in path:
            xs.extend([seg.start.real, seg.end.real])
            ys.extend([seg.start.imag, seg.end.imag])
        return complex(sum(xs)/len(xs), sum(ys)/len(ys))
    
    # Split compound paths into seperate paths
    def split_compound_paths(self):
        new_paths = []
        for path in self.paths:
            subpaths = path.continuous_subpaths()
            for sp in subpaths:
                new_paths.append(sp)
        self.paths = new_paths

    # Remove duplicate paths
    def dedupe_paths(self):
        unique = []
        seen = set()

        for p in self.paths:
            key = tuple(
                (round(seg.start.real, 4), round(seg.start.imag, 4),
                round(seg.end.real, 4), round(seg.end.imag, 4))
                for seg in p
            )
            if key not in seen:
                seen.add(key)
                unique.append(p)

        self.paths = unique

    # Save gcode into file
    def save(self):
        with open(self.output_file, "w") as f:
            f.write("\n".join(self.gcode))

    # Convert svg to gcode
    def run(self):
        self.add_header()
        self.convert_paths()
        self.add_footer()
        self.save()
