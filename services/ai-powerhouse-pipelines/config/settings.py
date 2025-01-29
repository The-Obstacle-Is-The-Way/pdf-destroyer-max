# config/settings.py

from pydantic import BaseSettings
from typing import Optional, Dict, List
import os

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Powerhouse Pipelines"
    
    # Model Settings
    MODEL_CACHE_DIR: str = "/app/data/models"
    MAX_BATCH_SIZE: int = 32
    
    # Pipeline Settings
    PARALLEL_PROCESSING: bool = True
    MAX_WORKERS: int = 4
    TIMEOUT: int = 300
    
    # Model Configurations
    NEURAL_MERGER_CONFIG: Dict = {
        "model_name": "microsoft/layoutlmv3-base",
        "max_length": 512,
        "batch_size": 16
    }
    
    QUALITY_SCORER_CONFIG: Dict = {
        "threshold": 0.8,
        "metrics": ["clarity", "completeness", "consistency"]
    }
    
    # Resource Settings
    GPU_MEMORY_FRACTION: float = 0.8
    CPU_THREADS: int = 4
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Storage
    TEMP_DIR: str = "/app/data/temp"
    OUTPUT_DIR: str = "/app/data/output"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

# config/logging_config.py

import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": "/app/logs/pipeline.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "root": {"level": "INFO", "handlers": ["console", "file"]},
    "loggers": {
        "pipeline": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}

# config/model_config.yaml

neural_merger:
  model_name: "microsoft/layoutlmv3-base"
  max_length: 512
  batch_size: 16
  use_gpu: true
  precision: "fp16"
  cache_dir: "/app/data/models/neural_merger"

quality_scoring:
  thresholds:
    clarity: 0.8
    completeness: 0.85
    consistency: 0.75
  metrics:
    - clarity
    - completeness
    - consistency
  cache_dir: "/app/data/models/quality_scoring"

document_qa:
  model_name: "deepset/roberta-base-squad2"
  max_length: 384
  doc_stride: 128
  batch_size: 8
  cache_dir: "/app/data/models/document_qa"

layout_genius:
  model_name: "microsoft/layoutlmv3-base"
  max_length: 512
  batch_size: 16
  cache_dir: "/app/data/models/layout_genius"