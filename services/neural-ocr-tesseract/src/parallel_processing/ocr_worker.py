# services/neural-ocr-tesseract/src/parallel_processing/ocr_worker.py

from typing import Dict, List, Optional
from pathlib import Path
import httpx
from loguru import logger
from ...orchestration.smart_orchestrator import ParallelProcessor, ProcessorResult

class OCRWorker(ParallelProcessor):
    """Worker class for parallel OCR processing"""
    
    def __init__(self, 
                 ocr_service_url: str = "http://ocr-tesseract:8004",
                 language: str = "eng",
                 dpi: int = 300):
        super().__init__("ocr_worker")
        self.ocr_service_url = ocr_service_url
        self.language = language
        self.dpi = dpi
        self.client = httpx.AsyncClient(timeout=300.0)
        logger.info(f"Initialized OCR worker with language={language}, dpi={dpi}")

    async def process_page(self, file_path: Path, page_number: int) -> ProcessorResult:
        """Process a single page with OCR"""
        try:
            # Prepare request to OCR service
            async with self.client as client:
                files = {
                    'file': ('document.pdf', file_path.read_bytes(), 'application/pdf')
                }
                data = {
                    'page': page_number,
                    'language': self.language,
                    'dpi': self.dpi,
                    'enhance_image': True
                }
                
                response = await client.post(
                    f"{self.ocr_service_url}/process_page",
                    files=files,
                    data=data
                )
                
                if response.status_code != 200:
                    raise Exception(f"OCR service error: {response.text}")
                
                result = response.json()
                
                return ProcessorResult(
                    processor_name=self.name,
                    page_number=page_number,
                    content=result['text'],
                    confidence=result.get('confidence', 0.5),
                    metadata={
                        'ocr_engine': 'tesseract',
                        'language': self.language,
                        'dpi': self.dpi,
                        'enhancement_applied': True,
                        'detected_languages': result.get('languages', []),
                        'processing_time': result.get('processing_time', 0)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error in OCR processing for page {page_number}: {str(e)}")
            raise

    async def process_document(self, file_path: Path, page_numbers: List[int]) -> Dict[int, ProcessorResult]:
        """Process multiple pages in parallel with batched OCR"""
        try:
            # Send batch request to OCR service
            async with self.client as client:
                files = {
                    'file': ('document.pdf', file_path.read_bytes(), 'application/pdf')
                }
                data = {
                    'pages': ','.join(map(str, page_numbers)),
                    'language': self.language,
                    'dpi': self.dpi,
                    'enhance_image': True,
                    'batch_mode': True
                }
                
                response = await client.post(
                    f"{self.ocr_service_url}/process_batch",
                    files=files,
                    data=data
                )
                
                if response.status_code != 200:
                    raise Exception(f"OCR service error: {response.text}")
                
                batch_results = response.json()
                
                # Convert to ProcessorResult objects
                results = {}
                for page_num, result in batch_results.items():
                    results[int(page_num)] = ProcessorResult(
                        processor_name=self.name,
                        page_number=int(page_num),
                        content=result['text'],
                        confidence=result.get('confidence', 0.5),
                        metadata={
                            'ocr_engine': 'tesseract',
                            'language': self.language,
                            'dpi': self.dpi,
                            'enhancement_applied': True,
                            'detected_languages': result.get('languages', []),
                            'processing_time': result.get('processing_time', 0)
                        }
                    )
                
                return results
                
        except Exception as e:
            logger.error(f"Error in batch OCR processing: {str(e)}")
            raise

    async def _enhance_image_quality(self, image_bytes: bytes) -> bytes:
        """Enhance image quality before OCR if needed"""
        # This would call your image enhancement service
        # For now, return original bytes
        return image_bytes

    def _calculate_confidence(self, text: str, ocr_confidence: float) -> float:
        """Calculate overall confidence score"""
        if not text.strip():
            return 0.0
            
        # Combine OCR confidence with text analysis
        text_score = min(1.0, len(text.split()) / 100)  # Text length factor
        alpha_ratio = sum(c.isalpha() for c in text) / len(text) if text else 0
        
        # Weight factors
        ocr_weight = 0.6
        text_weight = 0.2
        alpha_weight = 0.2
        
        final_score = (
            ocr_confidence * ocr_weight +
            text_score * text_weight +
            alpha_ratio * alpha_weight
        )
        
        return max(0.1, min(final_score, 1.0))