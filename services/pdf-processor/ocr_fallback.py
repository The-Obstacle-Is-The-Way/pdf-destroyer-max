from typing import Dict, List
import httpx
from loguru import logger
import asyncio
from io import BytesIO

class OCRServiceClient:
    """Client for communicating with OCR service."""
    
    def __init__(self, base_url: str = "http://ocr-tesseract:8004"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout
        
    async def process_pages(
        self,
        pdf_path: str,
        page_numbers: List[int]
    ) -> Dict[int, str]:
        """
        Send pages to OCR service for processing.
        
        Args:
            pdf_path: Path to the PDF file
            page_numbers: List of page numbers to process
            
        Returns:
            Dictionary mapping page numbers to extracted text
        """
        try:
            # Read PDF file
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
            
            # Prepare multipart form data
            files = {
                'file': ('document.pdf', BytesIO(pdf_data), 'application/pdf')
            }
            data = {
                'pages': ','.join(map(str, page_numbers))
            }
            
            # Send request to OCR service
            response = await self.client.post(
                f"{self.base_url}/process",
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                raise OCRServiceError(f"OCR service error: {response.text}")
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error in OCR service communication: {str(e)}")
            raise OCRServiceError(f"Failed to process pages: {str(e)}")

class OCRServiceError(Exception):
    """Custom exception for OCR service errors."""
    pass