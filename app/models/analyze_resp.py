from pydantic import BaseModel
from typing import List

class UploadAnalyzeResponse(BaseModel):
    job_id: str
    upload_path: str
    width: float
    height: float
    layout: str
    needs_rotation: bool

class DimensionCheckResponse(BaseModel):
    fits: bool
    width: float
    height: float
    max_x: float
    max_y: float
    required_scale: float

class ColourDetectResponse(BaseModel):
    colours: List[str]
    colour_count: int