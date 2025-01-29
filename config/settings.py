from pathlib import Path
from typing import Dict, Any
import yaml
import os
from dotenv import load_dotenv

class ProjectSettings:
    """Global project settings handling both environment and YAML configs."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.env = os.getenv("ENVIRONMENT", "development")
        self._load_environment()
        self._load_config()

    def _load_environment(self):
        """Load environment-specific variables."""
        env_file = self.base_dir / "config" / "environments" / f"{self.env}.env"
        if env_file.exists():
            load_dotenv(env_file)
        else:
            raise ValueError(f"Environment file not found: {env_file}")

    def _load_config(self):
        """Load and merge configuration from multiple sources."""
        # Service connection settings
        self.services = {
            'pdf_processor': {
                'host': os.getenv('PDF_PROCESSOR_HOST', 'localhost'),
                'port': int(os.getenv('PDF_PROCESSOR_PORT', '8003')),
                'base_url': os.getenv('PDF_PROCESSOR_URL', 'http://pdf-processor:8003')
            },
            'ocr_tesseract': {
                'host': os.getenv('OCR_HOST', 'localhost'),
                'port': int(os.getenv('OCR_PORT', '8004')),
                'base_url': os.getenv('OCR_URL', 'http://ocr-tesseract:8004')
            },
            'transformers_summarizer': {
                'host': os.getenv('SUMMARIZER_HOST', 'localhost'),
                'port': int(os.getenv('SUMMARIZER_PORT', '8005')),
                'base_url': os.getenv('SUMMARIZER_URL', 'http://transformers-summarizer:8005')
            }
        }

        # Storage paths
        self.paths = {
            'data': self.base_dir / 'data',
            'logs': self.base_dir / 'logs',
            'temp': self.base_dir / 'data' / 'temp',
            'input': self.base_dir / 'data' / 'input',
            'output': self.base_dir / 'data' / 'output'
        }

        # Ensure all directories exist
        for path in self.paths.values():
            path.mkdir(parents=True, exist_ok=True)

        # Processing settings
        self.processing = {
            'max_file_size': int(os.getenv('MAX_FILE_SIZE', '100')) * 1024 * 1024,  # in bytes
            'supported_formats': ['pdf', 'PDF'],
            'chunk_size': int(os.getenv('CHUNK_SIZE', '1000')),
            'batch_size': int(os.getenv('BATCH_SIZE', '10')),
            'timeout': int(os.getenv('PROCESSING_TIMEOUT', '300')),
            'retry_attempts': int(os.getenv('RETRY_ATTEMPTS', '3'))
        }

        # Security settings
        self.security = {
            'api_key_required': os.getenv('API_KEY_REQUIRED', 'false').lower() == 'true',
            'allowed_origins': os.getenv('ALLOWED_ORIGINS', '*').split(','),
            'ssl_verify': os.getenv('SSL_VERIFY', 'true').lower() == 'true'
        }

    @property
    def pdf_processor_settings(self) -> Dict[str, Any]:
        """Get PDF processor specific settings."""
        return {
            'service': self.services['pdf_processor'],
            'processing': self.processing,
            'paths': {k: str(v) for k, v in self.paths.items()},
            'security': self.security
        }

    def get_service_url(self, service_name: str) -> str:
        """Get the base URL for a specific service."""
        return self.services[service_name]['base_url']

settings = ProjectSettings()