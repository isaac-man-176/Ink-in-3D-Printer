# analyzer.py
import os
import pymupdf
from app.pipeline.pdf_to_svg import PdfToSvg
from app.config import PRINTERS, PEN_OFFSET_FWD

# Convert points to millimeters: 72 points = 25.4 mm
POINTS_TO_MM = 25.4 / 72


class PDFAnalyzer:
    """Handles PDF analysis and dimension checking"""

    @staticmethod
    def get_dimensions(pdf_path: str):
        """
        Get PDF dimensions and layout information in millimeters
        
        Returns:
            dict: width, height, layout, needs_rotation (dimensions in mm)
        """
        try:
            doc = pymupdf.open(pdf_path)
            page = doc.load_page(0)
            width = page.rect.width * POINTS_TO_MM
            height = page.rect.height * POINTS_TO_MM
            doc.close()

            layout = "portrait" if height >= width else "landscape"
            needs_rotation = layout == "portrait"

            return {
                "width": width,
                "height": height,
                "layout": layout,
                "needs_rotation": needs_rotation
            }
        except Exception as e:
            raise Exception(f"Failed to get dimensions: {str(e)}")

    @staticmethod
    def check_dimensions(pdf_path: str, printer: str, rotate: bool = False):
        """
        Check if PDF fits within printer dimensions
        
        Args:
            pdf_path: Path to PDF file
            printer: Printer name (must be in PRINTERS config)
            rotate: Whether PDF is rotated to landscape
        
        Returns:
            dict: fits, width, height, max_x, max_y, required_scale
        """
        if printer not in PRINTERS:
            raise ValueError(f"Unknown printer: {printer}")

        if not os.path.exists(pdf_path):
            raise ValueError(f"PDF not found: {pdf_path}")

        try:
            doc = pymupdf.open(pdf_path)
            page = doc.load_page(0)

            if rotate:
                page.set_rotation(90)

            width = page.rect.width * POINTS_TO_MM
            height = page.rect.height * POINTS_TO_MM
            doc.close()

            printer_config = PRINTERS[printer]
            max_x = printer_config["max_x"]
            max_y = printer_config["max_y"] - PEN_OFFSET_FWD

            fits = width <= max_x and height <= max_y

            if fits:
                scale = 1.0
            else:
                # Calculate scale needed
                scale_x = max_x / width
                scale_y = max_y / height
                scale = min(scale_x, scale_y)

            return {
                "fits": fits,
                "width": width,
                "height": height,
                "max_x": max_x,
                "max_y": max_y,
                "required_scale": scale if not fits else 1.0
            }

        except Exception as e:
            raise Exception(f"Failed to check dimensions: {str(e)}")

    @staticmethod
    def detect_colours(pdf_path: str, output_svg_path: str = None):
        """
        Detect colours in PDF by converting to SVG and splitting by colour
        
        Args:
            pdf_path: Path to PDF file
            output_svg_path: Optional path to save colour SVG. 
                           If None, uses temp location
        
        Returns:
            dict: colours (list of hex colours), colour_count
        """
        if not os.path.exists(pdf_path):
            raise ValueError(f"PDF not found: {pdf_path}")

        try:
            max_x = PRINTERS["A1"]["max_x"]
            max_y = PRINTERS["A1"]["max_y"] - PEN_OFFSET_FWD

            if output_svg_path is None:
                output_svg_path = pdf_path.replace(".pdf", "_colours.svg")

            pdf_to_svg = PdfToSvg(pdf_path, output_svg_path, max_x, max_y)
            width, height, temp_svg, colour_svgs = pdf_to_svg.run(split_colours=True)

            colours = list(colour_svgs.keys())

            return {
                "colours": colours,
                "colour_count": len(colours)
            }

        except Exception as e:
            raise Exception(f"Failed to detect colours: {str(e)}")
