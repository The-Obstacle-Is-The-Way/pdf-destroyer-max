"""
API routes module
"""
from .health import router as health_router
from .pdf_routes import router as pdf_router
from .summarization_routes import router as summarization_router
from .ocr_routes import router as ocr_router

__all__ = [
    'health_router',
    'pdf_router',
    'summarization_router',
    'ocr_router'
]
