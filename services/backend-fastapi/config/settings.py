# services/backend-fastapi/config/settings.py

from pydantic_settings import BaseSettings
from typing import List
import os
from functools import lru_cache

class Settings(BaseSettings):
    # API Settings
    api_version: str = "1.0.0"
    debug_mode: bool = os.getenv("DEBUG_MODE", True)
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", 8001))

    # Pipeline Service Settings
    pipeline_service_url: str = os.getenv(
        "PIPELINE_SERVICE_URL", 
        "http://ai-powerhouse-pipelines:8005"
    )
    processing_timeout: int = int(os.getenv("PROCESSING_TIMEOUT", 300))
    
    # Processing Settings
    min_text_length: int = int(os.getenv("MIN_TEXT_LENGTH", 50))
    tesseract_language: str = os.getenv("TESSERACT_LANGUAGE", "eng")
    image_quality: int = int(os.getenv("IMAGE_QUALITY", 300))
    
    # File Paths
    upload_dir: str = os.getenv("UPLOAD_DIR", "/app/data/uploads")
    processed_dir: str = os.getenv("PROCESSED_DIR", "/app/data/processed")
    failed_dir: str = os.getenv("FAILED_DIR", "/app/data/failed")
    file_retention_days: int = int(os.getenv("FILE_RETENTION_DAYS", 7))
    
    # CORS Settings
    cors_origins: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()