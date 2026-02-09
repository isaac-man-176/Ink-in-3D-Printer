# svg_to_gcode.py
from svgpathtools import svg2paths2, Path
import xml.etree.ElementTree as ET
import numpy as np
import re

class SvgToGCode:
    def __init__(self, svg_file, output_file, scale_factor=1.0, line_segments=50, retraction_height=50, plot_height=0.2, max_x=255, max_y=255, pen_offset_y=0):
        self.svg_file = svg_file
        self.output_file = output_file
        self.scale_factor = scale_factor
        self.line_segments = line_segments
        self.retraction_height = retraction_height
        self.plot_height = plot_height
        self.max_x = max_x
        self.max_y = max_y
        self.pen_offset_y = pen_offset_y

        # Load paths
        self.paths, self.attributes, self.svg_attributes = svg2paths2(self.svg_file)
        print("Loaded paths:", len(self.paths))

        # Apply SVG transforms
        self.apply_svg_transforms()

        # Remove duplicates
        self.dedupe_paths()

        # Detect compound paths (multiple disconnected subpaths) and offer to split
        compound_count = self._count_compound_paths(gap_threshold=1.0)
        if compound_count > 0:
            ans = input(f"Found {compound_count} compound paths (multiple subpaths). Split them into separate paths? (y/n): ").strip().lower()
            if ans == "y":
                self.detect_and_split_compound_paths(gap_threshold=1.0)

        # Drop any empty paths to avoid zero-length issues
        self.paths = [p for p in self.paths if len(p) > 0]

        # Sort paths to minimize printer head travel distance
        self.sort_paths()

        # Normalize first
        self.normalize_paths()
        
        # Filter out tiny paths (< 1mm)
        self.filter_tiny_paths(min_size=1.0)

        # Scale actual geometry
        self.scale_paths(scale_factor)

        self.gcode = []

    def apply_svg_transforms(self):
        tree = ET.parse(self.svg_file)
        root = tree.getroot()

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

        for elem in root.iter():
            if elem.tag.endswith("path"):
                combined = get_group_transform(elem)
                path_transforms.append(combined)

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

    def scale_paths(self, factor):
        for path in self.paths:
            for seg in path:
                seg.start *= factor
                seg.end *= factor
                if hasattr(seg, "control1"):
                    seg.control1 *= factor
                if hasattr(seg, "control2"):
                    seg.control2 *= factor

    def normalize_paths(self):
        xs = []
        ys = []

        for path in self.paths:
            for seg in path:
                xs.extend([seg.start.real, seg.end.real])
                ys.extend([seg.start.imag, seg.end.imag])

        if not xs or not ys:
            return  # nothing to normalize

        min_x = min(xs)
        min_y = min(ys)

        # Offset to start at (0, 0)
        offset = complex(-min_x, -min_y)

        for path in self.paths:
            for seg in path:
                seg.start += offset
                seg.end += offset
                if hasattr(seg, "control1"):
                    seg.control1 += offset
                if hasattr(seg, "control2"):
                    seg.control2 += offset
    def filter_tiny_paths(self, min_size=1.0):
        """Remove paths smaller than min_size (in mm)"""
        filtered = []
        for path in self.paths:
            xs = []
            ys = []
            for seg in path:
                xs.extend([seg.start.real, seg.end.real])
                ys.extend([seg.start.imag, seg.end.imag])
            
            if xs and ys:
                width = max(xs) - min(xs)
                height = max(ys) - min(ys)
                size = max(width, height)
                
                if size >= min_size:
                    filtered.append(path)
        
        if len(filtered) < len(self.paths):
            print(f"Filtered out {len(self.paths) - len(filtered)} tiny paths (< {min_size}mm)")
        
        self.paths = filtered

    def _count_compound_paths(self, gap_threshold=1.0):
        """Return number of paths that contain internal large gaps (i.e., compound paths)."""
        count = 0
        for path in self.paths:
            for i in range(len(path) - 1):
                end = path[i].end
                nxt = path[i + 1].start
                if abs(nxt - end) > gap_threshold:
                    count += 1
                    break
        return count

    def detect_and_split_compound_paths(self, gap_threshold=1.0):
        """Split paths that contain large internal gaps into separate paths.

        A gap is detected when the distance between a segment end and the next
        segment start exceeds `gap_threshold` (mm)."""
        new_paths = []
        split_total = 0
        for path in self.paths:
            current = []
            for i, seg in enumerate(path):
                current.append(seg)
                is_last = (i == len(path) - 1)
                if not is_last:
                    nxt_start = path[i + 1].start
                    if abs(nxt_start - seg.end) > gap_threshold:
                        # boundary between subpaths
                        new_paths.append(list(current))
                        split_total += 1
                        current = []
            if current:
                new_paths.append(list(current))

        if split_total > 0:
            print(f"Split {split_total} compound paths into separate subpaths.")
            self.paths = new_paths


    def add(self, line):
        self.gcode.append(line)

    def add_header(self):
        self.add("; ------------Initial Sequence------------")
        self.add("G92 E0          ;Reset extruder")
        self.add("M82             ;Absolute extrusion coordinates")
        self.add("G90             ;Absolute position coordinates")
        self.add(f"G1 Z{self.plot_height + self.retraction_height} ; pen up")
        self.add(f"G1 X0 Y{self.pen_offset_y} Z{self.plot_height} ")
        self.add(f"G1 X0.01 Y{self.pen_offset_y + 0.01} Z{self.plot_height} E0.001 F1200")
        self.add(f"G1 X0 Y{self.pen_offset_y} Z{self.plot_height} F3000")
        self.add("M0 Insert pen and press button to continue")
        self.add(f"G1 Z{self.plot_height + self.retraction_height} ; pen up")
        self.add("; ------------Initial Sequence------------")

    def add_footer(self):
        self.add("; ------------End Sequence------------")
        self.add("M84            ;Disable Motors")
        self.add("M0 Remove pen and press button to continue")
        self.add("; ------------End Sequence------------")

    def _get_path_start(self, path):
        return path[0].start if len(path) > 0 else complex(0, 0)

    def convert_paths(self):
        path_starts = [(i, self._get_centroid(path)) for i, path in enumerate(self.paths)]

        # Filter out any paths that somehow produced a dummy centroid
        path_starts = [(i, c) for i, c in path_starts if c is not None]

        path_starts.sort(key=lambda x: -x[1].imag)

        y_threshold = 5
        groups = []
        current_group = []
        last_y = None

        for idx, center in path_starts:
            if last_y is None or abs(center.imag - last_y) <= y_threshold:
                current_group.append((idx, center))
                last_y = center.imag
            else:
                if current_group:
                    groups.append(current_group)
                current_group = [(idx, center)]
                last_y = center.imag

        if current_group:
            groups.append(current_group)

        all_indices = []
        for group_idx, group in enumerate(groups):
            if group_idx % 2 == 0:
                group.sort(key=lambda x: x[1].real)
            else:
                group.sort(key=lambda x: -x[1].real)
            all_indices.extend([idx for idx, _ in group])

        for path_idx in all_indices:
            path = self.paths[path_idx]
            if len(path) == 0:
                continue

            first = True
            for segment in path:
                for i, t in enumerate(np.linspace(0, 1, self.line_segments)):
                    point = segment.point(t)
                    x, y = point.real, point.imag + self.pen_offset_y

                    if first and i == 0:
                        self.add(f"G1 X{x:.3f} Y{y:.3f} F3000")
                        self.add(f"G1 Z{self.plot_height} ; pen down")
                        first = False
                    else:
                        self.add(f"G1 X{x:.3f} Y{y:.3f} F2000")

            self.add(f"G1 Z{self.plot_height + self.retraction_height} ; pen up")

    def sort_paths(self):
        def centroid_tuple(path):
            xs = []
            ys = []
            for seg in path:
                xs.extend([seg.start.real, seg.end.real])
                ys.extend([seg.start.imag, seg.end.imag])
            if not xs or not ys:
                return (0.0, 0.0)
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
            return (cy, cx)

        self.paths.sort(key=centroid_tuple)

    def _get_centroid(self, path):
        xs = []
        ys = []
        for seg in path:
            xs.extend([seg.start.real, seg.end.real])
            ys.extend([seg.start.imag, seg.end.imag])
        if not xs or not ys:
            return None  # signals "ignore" to caller
        return complex(sum(xs) / len(xs), sum(ys) / len(ys))

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

    def save(self):
        # Remove consecutive duplicate movement lines before saving
        cleaned = []
        last = None
        for line in self.gcode:
            # Only dedupe identical consecutive lines (keep comments and distinct moves)
            if line == last:
                continue
            cleaned.append(line)
            last = line

        with open(self.output_file, "w") as f:
            f.write("\n".join(cleaned))

    def run(self):
        self.add_header()
        self.convert_paths()
        self.add_footer()
        self.save()
