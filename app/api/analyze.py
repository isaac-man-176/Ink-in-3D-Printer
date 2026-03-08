from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid

from app.models.analyze_req import DimensionCheckRequest, ColourDetectRequest
from app.models.analyze_resp import (UploadAnalyzeResponse, DimensionCheckResponse, ColourDetectResponse)
from app.pipeline.analyzer import PDFAnalyzer

router = APIRouter(prefix="/analyze", tags=["Analyze"])


class DimensionCheckRequest_JSON(DimensionCheckRequest):
    job_id: str
    upload_path: str

class ColourDetectRequest_JSON(ColourDetectRequest):
    job_id: str
    upload_path: str


@router.post("/upload", response_model=UploadAnalyzeResponse)
async def analyze_pdf(file: UploadFile = File(...)):
    """
    Upload PDF and get initial info: dimensions, layout
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")

    upload_dir = "storage/uploads"
    os.makedirs(upload_dir, exist_ok=True)

    job_id = str(uuid.uuid4())[:8]
    upload_path = os.path.join(upload_dir, f"{job_id}.pdf")

    try:
        with open(upload_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save failed: {str(e)}")

    try:
        # Use PDFAnalyzer pipeline to get dimensions
        analysis = PDFAnalyzer.get_dimensions(upload_path)

        return {
            "job_id": job_id,
            "upload_path": upload_path,
            "width": analysis["width"],
            "height": analysis["height"],
            "layout": analysis["layout"],
            "needs_rotation": analysis["needs_rotation"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-dimensions", response_model=DimensionCheckResponse)
async def check_dimensions(body: DimensionCheckRequest_JSON):
    """
    Check if PDF fits within printer dimensions, optionally with rotation
    """
    job_id = body.job_id
    upload_path = body.upload_path
    printer = body.printer
    rotate = body.rotate
    
    if not job_id or not printer:
        raise HTTPException(status_code=400, detail="job_id and printer required")

    if not os.path.exists(upload_path):
        raise HTTPException(status_code=404, detail="Upload not found")

    try:
        # Use PDFAnalyzer pipeline to check dimensions
        analysis = PDFAnalyzer.check_dimensions(upload_path, printer, rotate)
        return analysis

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect-colours", response_model=ColourDetectResponse)
async def detect_colours(body: ColourDetectRequest_JSON):
    """
    Detect colours in PDF (for multi-colour mode)
    """
    job_id = body.job_id
    upload_path = body.upload_path
    
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id required")
    
    if not os.path.exists(upload_path):
        raise HTTPException(status_code=404, detail="Upload not found")

    try:
        svg_path = os.path.join("storage/svgs", f"{job_id}_colours.svg")
        os.makedirs("storage/svgs", exist_ok=True)

        # Use PDFAnalyzer pipeline to detect colours
        analysis = PDFAnalyzer.detect_colours(upload_path, svg_path)

        return {
            "colours": analysis["colours"],
            "colour_count": analysis["colour_count"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
