import os
from pathlib import Path
from datetime import datetime
import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from loguru import logger
import shutil
import tempfile
import hashlib
from concurrent.futures import ThreadPoolExecutor

class PDFUtilities:
    """Utility functions for PDF processing operations."""
    
    @staticmethod
    def setup_directories(base_path: Path) -> Dict[str, Path]:
        """
        Creates and returns necessary directory structures.
        """
        directories = {
            'uploads': base_path / 'uploads',
            'processed': base_path / 'processed',
            'failed': base_path / 'failed',
            'temp': base_path / 'temp',
            'cache': base_path / 'cache'
        }
        
        for dir_path in directories.values():
            dir_path.mkdir(parents=True, exist_ok=True)
            
        return directories

    @staticmethod
    async def clean_old_files(directory: Path, max_age_hours: int = 24):
        """
        Removes files older than specified hours.
        """
        try:
            current_time = datetime.now().timestamp()
            async with asyncio.Lock():
                for file_path in directory.glob('*'):
                    if file_path.is_file():
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > max_age_hours * 3600:
                            file_path.unlink()
                            logger.info(f"Removed old file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning old files: {str(e)}")

    @staticmethod
    def calculate_file_hash(file_path: Path) -> str:
        """
        Calculates SHA-256 hash of a file.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @staticmethod
    async def save_result_callback(callback_url: str, result: Dict[str, Any]):
        """
        Sends processing results to callback URL.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(callback_url, json=result) as response:
                    if response.status != 200:
                        logger.error(f"Callback failed: {response.status}")
                    else:
                        logger.info(f"Callback successful: {callback_url}")
        except Exception as e:
            logger.error(f"Error sending callback: {str(e)}")

    @staticmethod
    async def create_temp_copy(file_path: Path) -> Path:
        """
        Creates a temporary copy of a file for processing.
        """
        temp_dir = Path(tempfile.gettempdir())
        temp_file = temp_dir / f"proc_{datetime.now().timestamp()}_{file_path.name}"
        await asyncio.to_thread(shutil.copy2, file_path, temp_file)
        return temp_file

class Cache:
    """Simple cache implementation for processing results."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> Optional[Dict]:
        """
        Retrieves cached result.
        """
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text())
            except Exception:
                return None
        return None

    def set(self, key: str, value: Dict):
        """
        Stores result in cache.
        """
        cache_file = self.cache_dir / f"{key}.json"
        try:
            cache_file.write_text(json.dumps(value))
        except Exception as e:
            logger.error(f"Cache write error: {str(e)}")

    async def cleanup(self, max_age_hours: int = 24):
        """
        Removes old cache entries.
        """
        await PDFUtilities.clean_old_files(self.cache_dir, max_age_hours)

class ProgressTracker:
    """Tracks processing progress for long-running tasks."""
    
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = datetime.now()

    def update(self, steps_completed: int = 1):
        """
        Updates progress and returns current percentage.
        """
        self.current_step += steps_completed
        return (self.current_step / self.total_steps) * 100

    def get_eta(self) -> Optional[float]:
        """
        Estimates time remaining based on progress.
        """
        if self.current_step == 0:
            return None
            
        elapsed = (datetime.now() - self.start_time).total_seconds()
        rate = self.current_step / elapsed
        remaining_steps = self.total_steps - self.current_step
        return remaining_steps / rate if rate > 0 else None

class ErrorHandler:
    """Handles and logs errors during processing."""
    
    @staticmethod
    def handle_processing_error(e: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handles processing errors and returns structured error info.
        """
        error_info = {
            "error_type": type(e).__name__,
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
            "context": context
        }
        
        logger.error(f"Processing error: {error_info}")
        return error_info

    @staticmethod
    async def move_to_failed(file_path: Path, failed_dir: Path, error_info: Dict[str, Any]):
        """
        Moves failed file to failed directory with error info.
        """
        try:
            # Create error info file
            error_file = failed_dir / f"{file_path.stem}_error.json"
            error_file.write_text(json.dumps(error_info))
            
            # Move failed file
            shutil.move(str(file_path), str(failed_dir / file_path.name))
            
        except Exception as e:
            logger.error(f"Error moving failed file: {str(e)}")
