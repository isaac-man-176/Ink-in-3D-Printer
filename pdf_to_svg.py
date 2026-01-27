import pymupdf
import pathlib
import re
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

        # NEW: remove white background rectangles
        svg_string = re.sub(r'<rect[^>]*fill="white"[^>]*/>', '', svg_string)

        temp_svg = pathlib.Path(self.svg_file)
        temp_svg.write_text(svg_string, encoding="utf-8")

        return width, height, temp_svg
    
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

        # svgutils scaling removed — scaling now happens in SvgToGCode
        fig = sg.fromfile(str(temp_svg))
        fig.save(self.svg_file)

        return scale

    def _ask_for_scale(self, width, height):
        print("\nCurrent dimensions:")
        print(f"  Width:  {width}")
        print(f"  Height: {height}")

        dim_choice = input(
            "\nWhich dimension do you want to change? (width/height): "
        ).strip().lower()

        if dim_choice == "width" or dim_choice == "w":
            new_width = float(input("Enter new width: "))
            print(new_width)
            return new_width / width

        elif dim_choice == "height" or dim_choice == "h":
            new_height = float(input("Enter new height: "))
            print(new_height)
            return new_height / height

        else:
            raise ValueError("Invalid dimension choice")

    def run(self):
        width, height, temp_svg = self.convert()
        scale = self.scale(width, height, temp_svg)
        self.scale_factor = scale  # NEW: store scale factor
