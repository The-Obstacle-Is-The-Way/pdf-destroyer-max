# backend-fastapi/api/routes/ocr_routes.py
from fastapi import APIRouter, UploadFile, File, Depends
from ..dependencies import get_ocr_service
from ..ocr_service import OCRService
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/ocr", tags=["ocr"])

@router.get("/health")
async def check_ocr_health(
    ocr_service: OCRService = Depends(get_ocr_service)
) -> Dict[str, Any]:
    return await ocr_service.health_check()

@router.post("/extract")
async def extract_text(
    file: UploadFile = File(...),
    ocr_service: OCRService = Depends(get_ocr_service)
) -> Dict[str, Any]:
    return await ocr_service.extract_text(file)