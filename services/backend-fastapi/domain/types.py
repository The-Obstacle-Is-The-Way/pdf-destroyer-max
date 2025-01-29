# services/backend-fastapi/domain/types.py

from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

class ProcessingStatus(str, Enum):
    """Status of document processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProcessorType(str, Enum):
    """Types of document processors"""
    TEXT_EXTRACTION = "text_extraction"
    OCR = "ocr"
    LAYOUT_ANALYSIS = "layout_analysis"
    TABLE_DETECTION = "table_detection"
    SUMMARIZATION = "summarization"

class DocumentType(str, Enum):
    """Supported document types"""
    PDF = "pdf"
    IMAGE = "image"
    SCANNED_PDF = "scanned_pdf"
    DIGITAL_PDF = "digital_pdf"

class ExportFormat(str, Enum):
    """Supported export formats"""
    PDF = "pdf"
    TEXT = "text"
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    CSV = "csv"

class ProcessingOptions(BaseModel):
    """Options for document processing"""
    processors: List[ProcessorType] = Field(
        default=[ProcessorType.TEXT_EXTRACTION],
        description="List of processors to run"
    )
    parallel_processing: bool = Field(
        default=True,
        description="Whether to run processors in parallel"
    )
    quality_threshold: float = Field(
        default=0.7,
        description="Minimum quality score threshold",
        ge=0.0,
        le=1.0
    )
    export_format: ExportFormat = Field(
        default=ExportFormat.PDF,
        description="Desired export format"
    )
    preserve_layout: bool = Field(
        default=True,
        description="Whether to preserve document layout"
    )

class ProcessingResult(BaseModel):
    """Result from a single processor"""
    processor_type: ProcessorType
    confidence_score: float = Field(ge=0.0, le=1.0)
    text_content: str
    metadata: Dict = Field(default_factory=dict)
    page_number: int
    bounding_boxes: Optional[List[Dict[str, float]]] = None

class DocumentMetadata(BaseModel):
    """Metadata for a document"""
    document_id: str
    filename: str
    file_size: int
    page_count: int
    document_type: DocumentType
    upload_time: datetime
    processing_status: ProcessingStatus
    processing_options: ProcessingOptions
    last_modified: datetime
    checksum: str

class ProcessingSummary(BaseModel):
    """Summary of document processing"""
    document_id: str
    status: ProcessingStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    processor_statuses: Dict[ProcessorType, ProcessingStatus]
    quality_scores: Dict[ProcessorType, float]
    processing_time: Optional[float] = None

class ErrorResponse(BaseModel):
    """Standardized error response"""
    error_code: str
    message: str
    details: Optional[Dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthStatus(BaseModel):
    """Service health status"""
    status: str
    version: str
    uptime: float
    processor_status: Dict[ProcessorType, bool]
    resource_usage: Dict[str, float]
    last_check: datetime = Field(default_factory=datetime.utcnow)