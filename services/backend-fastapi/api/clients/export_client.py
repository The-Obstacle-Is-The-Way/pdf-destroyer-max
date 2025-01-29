from typing import Optional, Dict, Any, List
import aiohttp
import asyncio
from datetime import datetime
from pydantic import BaseModel
import logging
from fastapi import HTTPException

class ExportFormat(BaseModel):
    format_type: str
    template_id: Optional[str]
    settings: Dict[str, Any]

class ExportRequest(BaseModel):
    document_id: str
    format: ExportFormat
    metadata: Optional[Dict[str, Any]]
    callback_url: Optional[str]

class ExportClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger("export_client")
        
        # Default headers
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Client-ID": "pdf-destroyer-max"
        }

    async def create_export_job(
        self,
        document_id: str,
        format_type: str,
        settings: Dict[str, Any],
        template_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new export job for document conversion
        """
        export_request = ExportRequest(
            document_id=document_id,
            format=ExportFormat(
                format_type=format_type,
                template_id=template_id,
                settings=settings
            ),
            metadata=metadata or {},
            callback_url=callback_url
        )

        endpoint = f"{self.base_url}/v1/exports"
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                for attempt in range(self.max_retries):
                    try:
                        async with session.post(
                            endpoint,
                            json=export_request.dict(exclude_none=True),
                            timeout=self.timeout
                        ) as response:
                            if response.status == 201:
                                return await response.json()
                            elif response.status == 429:
                                retry_after = int(response.headers.get('Retry-After', 5))
                                await asyncio.sleep(retry_after)
                                continue
                            else:
                                error_data = await response.json()
                                raise HTTPException(
                                    status_code=response.status,
                                    detail=error_data.get('detail', 'Export job creation failed')
                                )
                    except asyncio.TimeoutError:
                        if attempt == self.max_retries - 1:
                            raise HTTPException(
                                status_code=504,
                                detail="Export service timeout"
                            )
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        
        except Exception as e:
            self.logger.error(f"Export job creation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Export service error: {str(e)}"
            )

    async def get_export_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of an export job
        """
        endpoint = f"{self.base_url}/v1/exports/{job_id}"
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(endpoint, timeout=self.timeout) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Export job {job_id} not found"
                        )
                    else:
                        error_data = await response.json()
                        raise HTTPException(
                            status_code=response.status,
                            detail=error_data.get('detail', 'Failed to get export status')
                        )
        except Exception as e:
            self.logger.error(f"Failed to get export status: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Export status check failed: {str(e)}"
            )

    async def cancel_export_job(self, job_id: str) -> bool:
        """
        Cancel an ongoing export job
        """
        endpoint = f"{self.base_url}/v1/exports/{job_id}/cancel"
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(endpoint, timeout=self.timeout) as response:
                    if response.status == 200:
                        return True
                    elif response.status == 404:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Export job {job_id} not found"
                        )
                    else:
                        error_data = await response.json()
                        raise HTTPException(
                            status_code=response.status,
                            detail=error_data.get('detail', 'Failed to cancel export job')
                        )
        except Exception as e:
            self.logger.error(f"Failed to cancel export job: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Export job cancellation failed: {str(e)}"
            )

    async def get_supported_formats(self) -> List[Dict[str, Any]]:
        """
        Get list of supported export formats and their settings
        """
        endpoint = f"{self.base_url}/v1/exports/formats"
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(endpoint, timeout=self.timeout) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_data = await response.json()
                        raise HTTPException(
                            status_code=response.status,
                            detail=error_data.get('detail', 'Failed to get supported formats')
                        )
        except Exception as e:
            self.logger.error(f"Failed to get supported formats: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Format retrieval failed: {str(e)}"
            )