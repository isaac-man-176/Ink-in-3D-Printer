from svg_to_gcode import SvgToGCode
from pdf_to_svg import PdfToSvg

pdf_to_svg = PdfToSvg("sample.pdf", "drawing.svg", 255)
pdf_to_svg.run()

# pass the scale factor into SvgToGCode
svg_to_gcode = SvgToGCode("drawing.svg", "output.gcode", scale_factor=pdf_to_svg.scale_factor)
svg_to_gcode.run()
