# services/pdf-processor/src/parallel_processors/text_extractor.py

from typing import Dict, Optional
import fitz
from pathlib import Path
from loguru import logger
from ...orchestration.smart_orchestrator import ParallelProcessor, ProcessorResult

class ParallelTextExtractor(ParallelProcessor):
    def __init__(self, min_text_length: int = 50):
        super().__init__("text_extractor")
        self.min_text_length = min_text_length
        
    async def process_page(self, file_path: Path, page_number: int) -> ProcessorResult:
        try:
            doc = fitz.open(str(file_path))
            page = doc[page_number]
            text = page.get_text()
            doc.close()
            
            # Calculate confidence based on text length and characteristics
            confidence = self._calculate_confidence(text)
            
            return ProcessorResult(
                processor_name=self.name,
                page_number=page_number,
                content=text,
                confidence=confidence,
                metadata={
                    "text_length": len(text),
                    "word_count": len(text.split()),
                    "extraction_method": "native_pdf"
                }
            )
            
        except Exception as e:
            logger.error(f"Error extracting text from page {page_number}: {str(e)}")
            raise
            
    def _calculate_confidence(self, text: str) -> float:
        """Calculate confidence score based on text characteristics"""
        if not text.strip():
            return 0.0
            
        # Basic heuristics for confidence scoring
        score = 1.0
        
        # Length-based scoring
        if len(text) < self.min_text_length:
            score *= 0.5
            
        # Word-based scoring
        words = text.split()
        if len(words) < 10:
            score *= 0.7
            
        # Character distribution scoring
        alpha_ratio = sum(c.isalpha() for c in text) / len(text) if text else 0
        if alpha_ratio < 0.5:
            score *= 0.8
            
        return max(0.1, min(score, 1.0))  # Clamp between 0.1 and 1.0