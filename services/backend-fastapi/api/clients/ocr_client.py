# backend-fastapi/api/ocr_service.py
from typing import Dict, Any, Optional, BinaryIO
from fastapi import HTTPException, BackgroundTasks, UploadFile
import httpx
from datetime import datetime
import logging
from PIL import Image
import io

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self, settings):
        self.base_url = settings.ocr_service_url or "http://neural-ocr-tesseract:8002"
        self.timeout = httpx.Timeout(30.0)

    async def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )

    async def extract_text(self, file: UploadFile) -> Dict[str, Any]:
        try:
            async with await self._get_client() as client:
                files = {'file': (file.filename, await file.read(), file.content_type)}
                response = await client.post("/ocr", files=files)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise HTTPException(400, "Invalid image format")
            logger.error(f"OCR service error: {str(e)}")
            raise HTTPException(503, "OCR service unavailable")
        except Exception as e:
            logger.error(f"OCR processing error: {str(e)}")
            raise HTTPException(500, str(e))

    async def health_check(self) -> Dict[str, Any]:
        try:
            async with await self._get_client() as client:
                start = datetime.utcnow()
                response = await client.get("/health")
                latency = (datetime.utcnow() - start).total_seconds() * 1000

                if response.status_code == 200:
                    data = response.json()
                    return {
                        'healthy': True,
                        'latency_ms': latency,
                        'gpu': data.get('gpu'),
                        'service': data.get('service')
                    }
                return {'healthy': False}
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {'healthy': False}