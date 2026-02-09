import pymupdf
import pathlib
import re
import os
import xml.etree.ElementTree as ET
from lxml import etree as LET
from svgutils import transform as sg

class PdfToSvg:
    def __init__(self, pdf_file, svg_file, max_x, max_y):
        self.pdf_file = pdf_file
        self.svg_file = svg_file
        self.max_x = max_x
        self.max_y = max_y

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

        # Expand <use> and remove white elements
        self.expand_svg_uses(temp_svg)
        self.remove_white_elements(temp_svg)

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
        """Remove ANY SVG element that draws a white background."""
        parser = LET.XMLParser(remove_blank_text=True)
        tree = LET.parse(str(svg_path), parser)
        root = tree.getroot()

        white_values = {"white", "#fff", "#ffffff"}

        def is_white(elem):
            # fill="white"
            fill = elem.get("fill", "").lower().strip()
            if fill in white_values:
                return True

            # style="fill:#ffffff"
            style = elem.get("style", "").lower()
            if "fill:" in style:
                style_fill = style.split("fill:")[1].split(";")[0].strip()
                if style_fill in white_values:
                    return True

            return False

        # Remove elements with white fill
        for elem in root.xpath(".//*[@fill]"):
            if is_white(elem):
                parent = elem.getparent()
                if parent is not None:
                    parent.remove(elem)

        # Remove elements with white fill in style
        for elem in root.xpath(".//*[@style]"):
            if is_white(elem):
                parent = elem.getparent()
                if parent is not None:
                    parent.remove(elem)

        # Remove full-page background paths even without fill
        for elem in root.xpath(".//path[@d]"):
            d = elem.get("d", "").replace(",", " ").strip()
            # Matches M0 0 H816 V1056 H0 Z (any numbers)
            if d.startswith("M0 0") and "H" in d and "V" in d and d.endswith("Z"):
                parent = elem.getparent()
                if parent is not None:
                    parent.remove(elem)

        tree.write(str(svg_path), encoding="utf-8", xml_declaration=True, pretty_print=True)


    def scale(self, width, height, temp_svg):
        print(f"\nOriginal SVG size:")
        print(f"  Width:  {width}")
        print(f"  Height: {height}")

        fits = width <= self.max_x and height <= self.max_y

        if fits:
            choice = input(
                f"\nSVG is within {self.max_x}x{self.max_y}. "
                "Do you want to change the scale? (y/n): "
            ).strip().lower()

            if choice != "y":
                scale = 1.0
            else:
                scale = self._ask_for_scale(width, height)
        else:
            print(
                f"\nSVG exceeds {self.max_x}x{self.max_y}."
                "\nYou must scale it down."
            )
            scale = self._ask_for_scale(width, height)

        fig = sg.fromfile(str(temp_svg))
        fig.save(self.svg_file)

        return scale

    def _ask_for_scale(self, width, height):
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

            if new_width > self.max_x or new_height > self.max_y:
                print(f"\n❌ Dimensions exceed {self.max_x}x{self.max_y}. Try again.")
                continue

            print("\n✅ Dimensions accepted.")
            return scale

    def run(self):
        width, height, temp_svg = self.convert()
        layout = self.get_layout(width, height)

        print(f"\nCurrent layout: {layout}")
        print(f"  Width:  {width}")
        print(f"  Height: {height}")

        if layout == "portrait":
            ans = input("Do you want to rotate page into landscape? (y/n): ").strip().lower()
            if ans == "y":
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

                try:
                    os.remove(temp_pdf)
                except:
                    pass

                print("✓ Rotated to landscape.")
        else:
            ans = input("Do you want to rotate page into portrait? (y/n): ").strip().lower()
            if ans == "y":
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

                try:
                    os.remove(temp_pdf)
                except:
                    pass

                print("✓ Rotated to portrait.")

        print(f"\nLayout after rotation:")
        print(f"  Width:  {width}")
        print(f"  Height: {height}")

        scale = self.scale(width, height, temp_svg)
        self.scale_factor = scale
