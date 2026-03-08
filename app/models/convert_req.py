from pydantic import BaseModel, Field
from typing import Optional, Dict, Literal


class ConvertRequest(BaseModel):

    printer: Literal["A1 Mini", "P1S/P2S", "A1", "H2D"]
    mode: Literal["single", "multi"]
    
    line_segments: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Number of segments used to approximate curves"
    )

    # Transformation options
    rotate: bool = Field(
        default=False,
        description="Rotate PDF to landscape if needed"
    )
    
    scale: Optional[float] = Field(
        default=None,
        gt=0,
        description="Optional manual scale factor"
    )

    # Only used in multi-colour mode
    dock_positions: Optional[Dict[str, int]] = Field(
        default=None,
        description="Mapping of colour_hex → dock number (1-6)"
    )
    
    split_compound_paths: bool = Field(
        default=False,
        description="Split compound paths before conversion"
    )