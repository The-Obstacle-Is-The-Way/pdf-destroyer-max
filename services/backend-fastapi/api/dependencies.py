from functools import lru_cache
from config.settings import Settings, get_settings
from .summarization_service import SummarizationService
from .ocr_service import OCRService
from .pdf_pipeline import PDFPipelineService

@lru_cache()
def get_summarization_service(settings: Settings = get_settings()) -> SummarizationService:
    """Dependency provider for SummarizationService"""
    return SummarizationService(settings)

@lru_cache()
def get_ocr_service(settings: Settings = get_settings()) -> OCRService:
    """Dependency provider for OCRService"""
    return OCRService(settings)

@lru_cache()
def get_pdf_pipeline_service(settings: Settings = get_settings()) -> PDFPipelineService:
    """Dependency provider for PDFPipelineService"""
    return PDFPipelineService(settings)