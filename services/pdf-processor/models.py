from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

class ProcessingOptions(BaseModel):
    """Configuration options for PDF processing."""
    enable_ocr: bool = Field(default=True, description="Enable OCR for images and scanned documents")
    chunk_size: int = Field(default=1000, description="Maximum size of text chunks")
    min_text_length: int = Field(default=50, description="Minimum text length to consider a page as text-based")
    extract_images: bool = Field(default=True, description="Extract and process embedded images")
    language: str = Field(default="eng", description="Primary language for OCR processing")

class ProcessingStatus(BaseModel):
    """Status information for a processing task."""
    task_id: str
    filename: str
    status: str = Field(description="Current processing status (QUEUED, PROCESSING, COMPLETED, FAILED)")
    timestamp: datetime
    progress: Optional[float] = Field(default=0.0, description="Processing progress (0-100)")
    error: Optional[str] = None
    result: Optional['ProcessingResult'] = None

class PageContent(BaseModel):
    """Content and metadata for a single PDF page."""
    text: str
    has_images: bool
    needs_ocr: bool
    metadata: Dict = Field(default_factory=dict)
    images: Optional[List[Dict]] = None
    confidence_score: Optional[float] = None

class ProcessingResult(BaseModel):
    """Complete results of PDF processing."""
    task_id: str
    timestamp: datetime
    page_count: int
    chunk_count: int
    ocr_used: bool
    content: Dict[int, PageContent]
    summary: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

class ProcessingError(BaseModel):
    """Detailed error information."""
    error_code: str
    message: str
    timestamp: datetime
    details: Optional[Dict] = None

class ProcessingRequest(BaseModel):
    """Incoming request for PDF processing."""
    filename: str
    options: Optional[ProcessingOptions] = Field(default_factory=ProcessingOptions)
    callback_url: Optional[str] = None
    metadata: Optional[Dict] = None

class ImageMetadata(BaseModel):
    """Metadata for extracted images."""
    page_number: int
    index: int
    dimensions: tuple
    format: str
    size_bytes: int
    extracted: bool
    ocr_applied: bool
    ocr_confidence: Optional[float] = None

class ChunkMetadata(BaseModel):
    """Metadata for text chunks."""
    chunk_index: int
    page_number: int
    word_count: int
    character_count: int
    has_overlap: bool
    start_offset: int
    end_offset: int