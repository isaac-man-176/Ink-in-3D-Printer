import pymupdf
import pathlib
import re
import os
import xml.etree.ElementTree as ET
from lxml import etree as LET
from svgutils import transform as sg
import copy

class PdfToSvg:
    def __init__(self, pdf_file, svg_file, max_x, max_y):
        self.pdf_file = pdf_file
        self.svg_file = svg_file
        self.max_x = max_x
        self.max_y = max_y
        self.scale_factor = 1.0
        self.colour_svgs = {}

    def convert(self):
        doc = pymupdf.open(self.pdf_file)
        page = doc.load_page(0)

        width = page.rect.width
        height = page.rect.height

        svg_string = page.get_svg_image()
        doc.close()

        if not svg_string.strip():
            raise ValueError("Generated SVG is empty")

        temp_svg = pathlib.Path(self.svg_file)
        temp_svg.write_text(svg_string, encoding="utf-8")

        # Expand <use> tags
        self.expand_svg_uses(temp_svg)

        # Remove white shapes
        self.remove_white_elements(temp_svg)

        # Remove duplicate paths
        self.remove_overlapping_paths(temp_svg)

        # Remove Google Docs page rectangles
        self.remove_page_rectangles(temp_svg)

        return width, height, temp_svg

    def rotate_pdf_page(self):
        doc = pymupdf.open(self.pdf_file)
        page = doc.load_page(0)
        page.set_rotation(90)

        temp_pdf = self.pdf_file.replace('.pdf', '_rotated_temp.pdf')
        doc.save(temp_pdf)
        doc.close()

        return temp_pdf

    def get_layout(self, width, height):
        return "portrait" if height >= width else "landscape"

    def expand_svg_uses(self, svg_path):
        ET.register_namespace("", "http://www.w3.org/2000/svg")
        ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

        tree = ET.parse(svg_path)
        root = tree.getroot()

        ns = {
            "svg": "http://www.w3.org/2000/svg",
            "xlink": "http://www.w3.org/1999/xlink"
        }

        defs = root.find("svg:defs", ns)
        glyphs = {}
        if defs is not None:
            for elem in defs:
                if elem.tag.endswith("path") and "id" in elem.attrib:
                    glyphs[elem.attrib["id"]] = elem.attrib.get("d", "")

        for use in root.findall(".//svg:use", ns):
            href = use.attrib.get("{http://www.w3.org/1999/xlink}href")
            if not href:
                continue

            glyph_id = href.replace("#", "")
            if glyph_id not in glyphs:
                continue

            d = glyphs[glyph_id]
            transform = use.attrib.get("transform", "")

            new_path = ET.Element("{http://www.w3.org/2000/svg}path")
            new_path.set("d", d)
            if transform:
                new_path.set("transform", transform)

            parent = use.getparent() if hasattr(use, "getparent") else None
            if parent is not None:
                parent.append(new_path)
            else:
                root.append(new_path)

        for use in root.findall(".//svg:use", ns):
            parent = use.getparent() if hasattr(use, "getparent") else None
            if parent is not None:
                parent.remove(use)

        tree.write(svg_path, encoding="utf-8", xml_declaration=True)

    def remove_white_elements(self, svg_path):
        parser = LET.XMLParser(remove_blank_text=True)
        tree = LET.parse(str(svg_path), parser)
        root = tree.getroot()

        white_values = {"white", "#fff", "#ffffff"}

        def is_white(elem):
            fill = elem.get("fill", "").lower().strip()
            if fill in white_values:
                return True

            style = elem.get("style", "").lower()
            if "fill:" in style:
                style_fill = style.split("fill:")[1].split(";")[0].strip()
                if style_fill in white_values:
                    return True

            return False

        for elem in root.xpath(".//*[@fill]"):
            if elem.getparent().tag.endswith("defs"):
                continue
            if is_white(elem):
                parent = elem.getparent()
                if parent is not None:
                    parent.remove(elem)

        for elem in root.xpath(".//*[@style]"):
            if elem.getparent().tag.endswith("defs"):
                continue
            if is_white(elem):
                parent = elem.getparent()
                if parent is not None:
                    parent.remove(elem)

        # Remove GoodNotes/Docs white background rectangles
        for elem in root.xpath(".//path[@d]"):
            if elem.getparent().tag.endswith("defs"):
                continue
            d = elem.get("d", "").replace(",", " ").strip()
            if d.startswith("M0 0") and "H" in d and "V" in d and d.endswith("Z"):
                parent = elem.getparent()
                if parent is not None:
                    parent.remove(elem)

        tree.write(str(svg_path), encoding="utf-8", xml_declaration=True, pretty_print=True)

    def remove_overlapping_paths(self, svg_path):
        parser = LET.XMLParser(remove_blank_text=True)
        tree = LET.parse(str(svg_path), parser)
        root = tree.getroot()

        seen = set()
        remove_list = []

        for elem in root.xpath(".//path[@d]"):
            d = elem.get("d", "").strip()
            key = d.replace(" ", "").replace(",", "")

            if key in seen:
                remove_list.append(elem)
            else:
                seen.add(key)

        for elem in remove_list:
            parent = elem.getparent()
            if parent is not None:
                parent.remove(elem)

        if remove_list:
            print(f"Removed {len(remove_list)} overlapping duplicate paths")

        tree.write(str(svg_path), encoding="utf-8", xml_declaration=True, pretty_print=True)

    # -------------------------------------------------------------
    # Remove Google Docs page rectangles (the giant M0 0 Hxxx Vyyy H0 Z)
    # -------------------------------------------------------------
    def remove_page_rectangles(self, svg_path):
        parser = LET.XMLParser(remove_blank_text=True)
        tree = LET.parse(str(svg_path), parser)
        root = tree.getroot()

        def is_page_rect(d):
            if not d:
                return False
            d_clean = d.replace(" ", "").replace(",", "").upper()
            return d_clean.startswith("M00H") and "V" in d_clean and d_clean.endswith("Z")

        remove_list = []

        for elem in root.xpath(".//svg:path", namespaces={"svg": "http://www.w3.org/2000/svg"}):
            d = elem.get("d", "")
            if is_page_rect(d):
                # Skip the one inside <defs> (clipPath)
                parent = elem.getparent()
                if parent is not None and parent.tag.endswith("defs"):
                    continue
                remove_list.append(elem)

        for elem in remove_list:
            parent = elem.getparent()
            if parent is not None:
                parent.remove(elem)

        if remove_list:
            print(f"Removed {len(remove_list)} Google Docs page rectangles")

        tree.write(str(svg_path), encoding="utf-8", xml_declaration=True, pretty_print=True)

    # -------------------------------------------------------------
    # Split by colour, uncoloured → black
    # -------------------------------------------------------------
    def split_by_colour(self, svg_path):
        parser = LET.XMLParser(remove_blank_text=True)
        tree = LET.parse(str(svg_path), parser)
        root = tree.getroot()

        ns = {"svg": "http://www.w3.org/2000/svg"}

        colour_groups = {}
        uncoloured_key = "000000"

        # Identify clipPath rectangle so we don't include it
        clip_rect_d = None
        defs = root.find("svg:defs", ns)
        if defs is not None:
            cp = defs.find("svg:clipPath", ns)
            if cp is not None:
                p = cp.find("svg:path", ns)
                if p is not None:
                    clip_rect_d = p.get("d", "").replace(" ", "").replace(",", "")

        elements = root.xpath(".//svg:path | .//svg:use", namespaces=ns)

        for elem in elements:
            # Skip clipPath rectangle
            d = elem.get("d", "")
            if d:
                d_key = d.replace(" ", "").replace(",", "")
                if clip_rect_d and d_key == clip_rect_d:
                    continue

            fill = elem.get("fill")
            stroke = elem.get("stroke")
            style = elem.get("style", "")

            colour = None

            # 1. Prefer fill if present and not "none"
            if fill and fill.lower() not in ("none", "transparent"):
                colour = fill

            # 2. Otherwise use stroke if present
            elif stroke and stroke.lower() not in ("none", "transparent"):
                colour = stroke

            # 3. Otherwise check style="fill:..."
            elif "fill:" in style:
                c = style.split("fill:")[1].split(";")[0].strip()
                if c.lower() not in ("none", "transparent"):
                    colour = c

            # 4. Otherwise check style="stroke:..."
            elif "stroke:" in style:
                c = style.split("stroke:")[1].split(";")[0].strip()
                if c.lower() not in ("none", "transparent"):
                    colour = c

            # 5. Default to black
            if not colour:
                colour = uncoloured_key

            # Normalize hex
            colour = colour.lower().strip()
            if colour.startswith("#"):
                colour = colour[1:]
            if len(colour) == 3:
                colour = "".join([c * 2 for c in colour])
            if not re.fullmatch(r"[0-9a-f]{6}", colour):
                colour = uncoloured_key

            if colour not in colour_groups:
                colour_groups[colour] = []
            colour_groups[colour].append(elem)

        output = {}

        for colour, elems in colour_groups.items():
            new_svg = LET.Element(root.tag, nsmap=root.nsmap)

            for attr in ["viewBox", "width", "height"]:
                if attr in root.attrib:
                    new_svg.set(attr, root.attrib[attr])

            defs = root.find("svg:defs", ns)
            if defs is not None:
                new_svg.append(copy.deepcopy(defs))

            for e in elems:
                new_svg.append(copy.deepcopy(e))

            out_path = svg_path.with_name(f"{svg_path.stem}_{colour}.svg")
            LET.ElementTree(new_svg).write(
                str(out_path),
                encoding="utf-8",
                pretty_print=True,
                xml_declaration=True
            )
            output[colour] = str(out_path)

        print("\nColour layers created:")
        for c in output:
            print(f"  #{c} -> {output[c]}")

        return output




    def run(self, split_colours=True):
        width, height, temp_svg = self.convert()
        layout = self.get_layout(width, height)

        # Auto-rotate if portrait
        if layout == "portrait":
            temp_pdf = self.rotate_pdf_page()
            doc = pymupdf.open(temp_pdf)
            page = doc.load_page(0)
            width = page.rect.width
            height = page.rect.height
            svg_string = page.get_svg_image()
            doc.close()

            if svg_string.strip():
                temp_svg.write_text(svg_string, encoding="utf-8")
                self.expand_svg_uses(temp_svg)
                self.remove_white_elements(temp_svg)
                self.remove_overlapping_paths(temp_svg)
                self.remove_page_rectangles(temp_svg)

            try:
                os.remove(temp_pdf)
            except:
                pass

        # Auto-scale if exceeds bounds
        scale = self._auto_scale(width, height, temp_svg)
        self.scale_factor = scale

        if split_colours:
            self.colour_svgs = self.split_by_colour(temp_svg)
        else:
            self.colour_svgs = {}

        return width, height, temp_svg, self.colour_svgs

    def _auto_scale(self, width, height, temp_svg):
        """Auto-scale SVG if it exceeds max dimensions"""
        if width <= self.max_x and height <= self.max_y:
            return 1.0
        
        # Scale to fit within bounds
        scale_x = self.max_x / width if width > self.max_x else 1.0
        scale_y = self.max_y / height if height > self.max_y else 1.0
        scale = min(scale_x, scale_y)
        
        # Apply scaling to SVG
        parser = LET.XMLParser(remove_blank_text=True)
        tree = LET.parse(str(temp_svg), parser)
        root = tree.getroot()
        
        if "viewBox" in root.attrib:
            root.set("viewBox", root.attrib["viewBox"])
        
        root.set("width", f"{width * scale}")
        root.set("height", f"{height * scale}")
        
        tree.write(str(temp_svg), encoding="utf-8", xml_declaration=True, pretty_print=True)
        
        return scale
