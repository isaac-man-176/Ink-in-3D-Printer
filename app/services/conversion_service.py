from app.pipeline.pdf_to_svg import PdfToSvg
from app.pipeline.svg_to_gcode import SvgToGCode
from app.pipeline.multi_colour_manager import MultiColourManager
from app.models.convert_req import ConvertRequest
from app.config import PRINTERS, PEN_OFFSET_FWD, RETRACT_HEIGHT, PLOT_HEIGHT
import os
import uuid

class ConversionService:
    def __init__(self):
        self.storage_dir = "storage"
        self.svgs_dir = os.path.join(self.storage_dir, "svgs")
        self.gcode_dir = os.path.join(self.storage_dir, "gcode")
        
        # Create directories if they don't exist
        os.makedirs(self.svgs_dir, exist_ok=True)
        os.makedirs(self.gcode_dir, exist_ok=True)

    def convert(self, pdf_path: str, request: ConvertRequest):

        printer = request.printer
        mode = request.mode
        line_segments = request.line_segments
        dock_positions = request.dock_positions

        printer_config = PRINTERS[printer]

        max_x = printer_config["max_x"]
        max_y = printer_config["max_y"] - PEN_OFFSET_FWD

        # Generate unique ID for this job
        job_id = str(uuid.uuid4())[:8]
        
        svg_path = os.path.join(self.svgs_dir, f"{job_id}_drawing.svg")
        gcode_path = os.path.join(self.gcode_dir, f"{job_id}_output.gcode")

        pdf_to_svg = PdfToSvg(pdf_path, svg_path, max_x, max_y)

        width, height, temp_svg, colour_svgs = pdf_to_svg.run(
            split_colours=(mode == "multi")
        )

        if mode == "single":
            svg_to_gcode = SvgToGCode(
                svg_file=svg_path,
                output_file=gcode_path,
                scale_factor=pdf_to_svg.scale_factor,
                line_segments=line_segments,
                retraction_height=RETRACT_HEIGHT,
                plot_height=PLOT_HEIGHT,
                max_x=max_x,
                max_y=max_y,
                pen_offset_y=PEN_OFFSET_FWD
            )

            svg_to_gcode.run()

            return {
                "job_id": job_id,
                "svg": svg_path,
                "gcode": gcode_path
            }

        else:
            multi_gcode_path = os.path.join(self.gcode_dir, f"{job_id}_multicolour.gcode")
            
            manager = MultiColourManager(
                colour_svgs=colour_svgs,
                output_file=multi_gcode_path,
                scale_factor=pdf_to_svg.scale_factor,
                line_segments=line_segments,
                retraction_height=RETRACT_HEIGHT,
                plot_height=PLOT_HEIGHT,
                max_x=max_x,
                max_y=max_y,
                pen_offset_y=PEN_OFFSET_FWD,
                dock_positions=dock_positions
            )

            manager.assemble()

            return {
                "job_id": job_id,
                "gcode": multi_gcode_path,
                "colours": list(colour_svgs.keys())
            }