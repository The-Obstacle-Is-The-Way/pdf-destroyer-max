# backend-fastapi/api/clients/pipeline_client.py

import os
import httpx
import asyncio
from typing import Dict, Any, Optional
from functools import lru_cache
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

class PipelineError(Exception):
    """Custom exception for pipeline errors"""
    pass

class PipelineRequest(BaseModel):
    """Request model for pipeline processing"""
    document_data: bytes
    task_id: str
    file_name: str
    config: Optional[Dict] = None

class PipelineClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("AI_POWERHOUSE_URL", "http://pipelines:8005")
        self.client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()
        self.timeout = httpx.Timeout(timeout=300.0)  # 5 minutes timeout
        
    async def __aenter__(self):
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        """Create httpx client if not exists"""
        if self.client is None:
            async with self._lock:
                if self.client is None:  # Double-check pattern
                    self.client = httpx.AsyncClient(
                        base_url=self.base_url,
                        timeout=self.timeout
                    )
                    logger.info(f"Established connection to Pipeline service at {self.base_url}")

    async def close(self):
        """Close httpx client"""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def _ensure_connection(self):
        """Ensure we have an active client"""
        if self.client is None:
            await self.connect()

    async def process_document(self, 
                             document_data: bytes, 
                             task_id: str, 
                             file_name: str, 
                             config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a document through the pipeline service
        
        Args:
            document_data: Binary content of the document
            task_id: Unique identifier for the task
            file_name: Name of the original file
            config: Optional configuration parameters
            
        Returns:
            Dict containing processing results
        """
        await self._ensure_connection()
        
        try:
            request = PipelineRequest(
                document_data=document_data,
                task_id=task_id,
                file_name=file_name,
                config=config
            )
            
            response = await self.client.post(
                "/process",
                json=request.dict(),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully processed document {task_id}")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error processing document {task_id}: {str(e)}")
            raise PipelineError(f"Pipeline service HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing document {task_id}: {str(e)}")
            raise PipelineError(f"Pipeline service error: {str(e)}")

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a pipeline task"""
        await self._ensure_connection()
        
        try:
            response = await self.client.get(f"/tasks/{task_id}/status")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting task status {task_id}: {str(e)}")
            raise PipelineError(f"Status check HTTP error: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting task status {task_id}: {str(e)}")
            raise PipelineError(f"Status check error: {str(e)}")

    async def get_service_health(self) -> Dict[str, Any]:
        """Check health of the pipeline service"""
        await self._ensure_connection()
        
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Pipeline service health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

@lru_cache()
def get_pipeline_client() -> PipelineClient:
    """Get or create a pipeline client instance"""
    return PipelineClient()