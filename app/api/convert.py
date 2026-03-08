from fastapi import APIRouter, HTTPException
import os

from app.models.convert_req import ConvertRequest
from app.models.convert_resp import ConvertResponse
from app.services.conversion_service import ConversionService

router = APIRouter(prefix="/convert", tags=["Convert"])
service = ConversionService()


class ConvertRequest_JSON(ConvertRequest):
    job_id: str
    upload_path: str


@router.post("", response_model=ConvertResponse)
async def convert_pdf(body: ConvertRequest_JSON):
    """
    Convert PDF to G-code via pre-uploaded file
    """

    try:
        if not os.path.exists(body.upload_path):
            raise HTTPException(status_code=404, detail="Upload not found")

        # Build ConvertRequest for service
        request_data = ConvertRequest(
            printer=body.printer,
            mode=body.mode,
            line_segments=body.line_segments,
            rotate=body.rotate,
            scale=body.scale,
            dock_positions=body.dock_positions,
            split_compound_paths=body.split_compound_paths
        )

        result = service.convert(
            pdf_path=body.upload_path,
            request=request_data
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))