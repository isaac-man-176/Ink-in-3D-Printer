from pydantic import BaseModel
from typing import Optional, List

class ConvertResponse(BaseModel):
    gcode: str
    svg: Optional[str] = None
    colours: Optional[List[str]] = None