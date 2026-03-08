from pydantic import BaseModel, Field
from typing import Literal


class DimensionCheckRequest(BaseModel):
    printer: Literal["A1 Mini", "P1S/P2S", "A1", "H2D"] = Field(
        ..., description="Target printer model"
    )

    rotate: bool = Field(
        default=False,
        description="Rotate PDF 90 degrees before checking dimensions"
    )

class ColourDetectRequest(BaseModel):
    """Pipeline request - without job tracking"""
    pass