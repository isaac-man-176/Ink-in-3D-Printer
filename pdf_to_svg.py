# pdf_to_svg.py
import pymupdf
import pathlib
import re
import xml.etree.ElementTree as ET
from svgutils import transform as sg

class PdfToSvg:
    def __init__(self, pdf_file, svg_file, max_size):
        self.pdf_file = pdf_file
        self.svg_file = svg_file
        self.max_size = max_size

    def convert(self):
        doc = pymupdf.open(self.pdf_file)
        page = doc.load_page(0)

        width = page.rect.width
        height = page.rect.height

        svg_string = page.get_svg_image()
        doc.close()

        if not svg_string.strip():
            raise ValueError("Generated SVG is empty")

        # remove white background rectangles
        svg_string = re.sub(r'<rect[^>]*fill="white"[^>]*/>', '', svg_string)

        temp_svg = pathlib.Path(self.svg_file)
        temp_svg.write_text(svg_string, encoding="utf-8")

        # ⭐ NEW: expand <use> into <path>
        self.expand_svg_uses(temp_svg)

        return width, height, temp_svg

    def expand_svg_uses(self, svg_path):
        ET.register_namespace("", "http://www.w3.org/2000/svg")
        ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

        tree = ET.parse(svg_path)
        root = tree.getroot()

        ns = {
            "svg": "http://www.w3.org/2000/svg",
            "xlink": "http://www.w3.org/1999/xlink"
        }

        # Collect glyph paths from <defs>
        defs = root.find("svg:defs", ns)
        glyphs = {}
        if defs is not None:
            for elem in defs:
                if elem.tag.endswith("path") and "id" in elem.attrib:
                    glyphs[elem.attrib["id"]] = elem.attrib.get("d", "")

        # Expand <use> elements
        for use in root.findall(".//svg:use", ns):
            href = use.attrib.get("{http://www.w3.org/1999/xlink}href")
            if not href:
                continue

            glyph_id = href.replace("#", "")
            if glyph_id not in glyphs:
                continue

            d = glyphs[glyph_id]
            transform = use.attrib.get("transform", "")

            # Create new <path>
            new_path = ET.Element("{http://www.w3.org/2000/svg}path")
            new_path.set("d", d)
            if transform:
                new_path.set("transform", transform)

            # Insert next to <use>
            parent = use.getparent() if hasattr(use, "getparent") else None
            if parent is not None:
                parent.append(new_path)
            else:
                root.append(new_path)

        # Remove <use> elements
        for use in root.findall(".//svg:use", ns):
            parent = use.getparent() if hasattr(use, "getparent") else None
            if parent is not None:
                parent.remove(use)

        # Save updated SVG (namespace preserved)
        tree.write(svg_path, encoding="utf-8", xml_declaration=True)


    def scale(self, width, height, temp_svg):
        print(f"\nOriginal SVG size:")
        print(f"  Width:  {width}")
        print(f"  Height: {height}")

        fits = max(width, height) <= self.max_size

        if fits:
            choice = input(
                f"\nSVG is within {self.max_size}x{self.max_size}. "
                "Do you want to change the scale? (y/n): "
            ).strip().lower()

            if choice != "y":
                scale = 1.0
            else:
                scale = self._ask_for_scale(width, height)
        else:
            print(
                f"\nSVG exceeds {self.max_size}x{self.max_size}."
                "\nYou must scale it down."
            )
            scale = self._ask_for_scale(width, height)

        fig = sg.fromfile(str(temp_svg))
        fig.save(self.svg_file)

        return scale

    def _ask_for_scale(self, width, height):
        MAX = self.max_size

        while True:
            print("\nCurrent dimensions:")
            print(f"  Width:  {width}")
            print(f"  Height: {height}")

            dim_choice = input(
                "\nWhich dimension do you want to change? (width/height): "
            ).strip().lower()

            if dim_choice in ("width", "w"):
                try:
                    new_width = float(input("Enter new width: ").strip())
                except ValueError:
                    print("Invalid number, try again.")
                    continue

                scale = new_width / width
                new_height = height * scale

            elif dim_choice in ("height", "h"):
                try:
                    new_height = float(input("Enter new height: ").strip())
                except ValueError:
                    print("Invalid number, try again.")
                    continue

                scale = new_height / height
                new_width = width * scale

            else:
                print("Please enter 'width' or 'height'.")
                continue

            print("\nScaled dimensions:")
            print(f"  Width:  {new_width}")
            print(f"  Height: {new_height}")

            if new_width > MAX or new_height > MAX:
                print(f"\n❌ One or both dimensions exceed {MAX}. Try again.")
                continue

            print("\n✅ Dimensions accepted.")
            return scale

    def run(self):
        width, height, temp_svg = self.convert()
        scale = self.scale(width, height, temp_svg)
        self.scale_factor = scale
