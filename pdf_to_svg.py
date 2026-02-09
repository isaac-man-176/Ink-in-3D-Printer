# pdf_to_svg.py
import pymupdf
import pathlib
import re
import os
import xml.etree.ElementTree as ET
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

        # remove white background rectangles
        svg_string = re.sub(r'<rect[^>]*fill="white"[^>]*/>', '', svg_string)

        temp_svg = pathlib.Path(self.svg_file)
        temp_svg.write_text(svg_string, encoding="utf-8")

        # expand <use> into <path>
        self.expand_svg_uses(temp_svg)

        return width, height, temp_svg

    def rotate_pdf_page(self):
        """Rotate the PDF page by 90 degrees clockwise"""
        doc = pymupdf.open(self.pdf_file)
        page = doc.load_page(0)
        
        # Set rotation: 90 degrees clockwise
        page.set_rotation(90)
        
        # Save temporary rotated PDF
        temp_pdf = self.pdf_file.replace('.pdf', '_rotated_temp.pdf')
        doc.save(temp_pdf)
        doc.close()
        
        return temp_pdf

    def get_layout(self, width, height):
        """Determine if layout is portrait or landscape"""
        if height >= width:
            return "portrait"
        else:
            return "landscape"

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
        
        # Ask about rotation
        if layout == "portrait":
            ans = input("Do you want to rotate page into landscape? (y/n): ").strip().lower()
            if ans == "y":
                temp_pdf = self.rotate_pdf_page()
                # Re-convert with rotated PDF
                doc = pymupdf.open(temp_pdf)
                page = doc.load_page(0)
                width = page.rect.width
                height = page.rect.height
                svg_string = page.get_svg_image()
                doc.close()
                
                if svg_string.strip():
                    svg_string = re.sub(r'<rect[^>]*fill="white"[^>]*/>', '', svg_string)
                    temp_svg.write_text(svg_string, encoding="utf-8")
                    self.expand_svg_uses(temp_svg)
                
                # Clean up temp PDF
                try:
                    os.remove(temp_pdf)
                except:
                    pass
                
                print("✓ Rotated to landscape.")
        else:
            ans = input("Do you want to rotate page into portrait? (y/n): ").strip().lower()
            if ans == "y":
                temp_pdf = self.rotate_pdf_page()
                # Re-convert with rotated PDF
                doc = pymupdf.open(temp_pdf)
                page = doc.load_page(0)
                width = page.rect.width
                height = page.rect.height
                svg_string = page.get_svg_image()
                doc.close()
                
                if svg_string.strip():
                    svg_string = re.sub(r'<rect[^>]*fill="white"[^>]*/>', '', svg_string)
                    temp_svg.write_text(svg_string, encoding="utf-8")
                    self.expand_svg_uses(temp_svg)
                
                # Clean up temp PDF
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
