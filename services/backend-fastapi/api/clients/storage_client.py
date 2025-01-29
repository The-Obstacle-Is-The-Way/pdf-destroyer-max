from typing import Optional, Dict, Any, BinaryIO, Union, List
import aiohttp
import asyncio
from datetime import datetime, timedelta
import mimetypes
import hashlib
from urllib.parse import urljoin
import logging
from fastapi import HTTPException, UploadFile
import aiofiles
import os

class StorageClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        bucket_name: str,
        timeout: int = 60,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.bucket_name = bucket_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger("storage_client")
        
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "X-Bucket-Name": bucket_name
        }

    async def upload_file(
        self,
        file: Union[UploadFile, BinaryIO, str],
        destination_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to storage with retry logic and chunked upload support
        """
        if isinstance(file, str) and os.path.exists(file):
            async with aiofiles.open(file, 'rb') as f:
                file_content = await f.read()
        elif isinstance(file, UploadFile):
            file_content = await file.read()
        else:
            raise ValueError("Invalid file input")

        # Determine content type
        if not content_type:
            if isinstance(file, UploadFile):
                content_type = file.content_type
            else:
                content_type = mimetypes.guess_type(destination_path)[0] or 'application/octet-stream'

        # Calculate file hash for integrity check
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Prepare upload request
        upload_url = f"{self.base_url}/v1/storage/upload"
        
        headers = {
            **self.headers,
            "Content-Type": content_type,
            "X-File-Hash": file_hash
        }
        
        if metadata:
            headers.update({f"X-Metadata-{k}": v for k, v in metadata.items()})

        try:
            async with aiohttp.ClientSession() as session:
                for attempt in range(self.max_retries):
                    try:
                        # Get upload URL with signed policy
                        async with session.post(
                            upload_url,
                            json={
                                "path": destination_path,
                                "content_type": content_type,
                                "size": len(file_content)
                            },
                            headers=self.headers,
                            timeout=self.timeout
                        ) as response:
                            if response.status == 200:
                                upload_data = await response.json()
                                upload_url = upload_data["upload_url"]
                                
                                # Perform actual upload
                                async with session.put(
                                    upload_url,
                                    data=file_content,
                                    headers=headers,
                                    timeout=self.timeout
                                ) as upload_response:
                                    if upload_response.status in (200, 201):
                                        return {
                                            "path": destination_path,
                                            "size": len(file_content),
                                            "content_type": content_type,
                                            "hash": file_hash,
                                            "metadata": metadata
                                        }
                                    else:
                                        error_data = await upload_response.json()
                                        raise HTTPException(
                                            status_code=upload_response.status,
                                            detail=error_data.get('detail', 'Upload failed')
                                        )
                            
                            elif response.status == 429:
                                retry_after = int(response.headers.get('Retry-After', 5))
                                await asyncio.sleep(retry_after)
                                continue
                            else:
                                error_data = await response.json()
                                raise HTTPException(
                                    status_code=response.status,
                                    detail=error_data.get('detail', 'Failed to initiate upload')
                                )
                                
                    except asyncio.TimeoutError:
                        if attempt == self.max_retries - 1:
                            raise HTTPException(
                                status_code=504,
                                detail="Storage service timeout"
                            )
                        await asyncio.sleep(2 ** attempt)
                        
        except Exception as e:
            self.logger.error(f"File upload failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Storage service error: {str(e)}"
            )

    async def download_file(self, file_path: str) -> bytes:
        """
        Download a file from storage
        """
        download_url = f"{self.base_url}/v1/storage/download"
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get download URL
                async with session.post(
                    download_url,
                    json={"path": file_path},
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        download_data = await response.json()
                        file_url = download_data["download_url"]
                        
                        # Download file
                        async with session.get(file_url, timeout=self.timeout) as download_response:
                            if download_response.status == 200:
                                return await download_response.read()
                            else:
                                error_data = await download_response.json()
                                raise HTTPException(
                                    status_code=download_response.status,
                                    detail=error_data.get('detail', 'Download failed')
                                )
                    elif response.status == 404:
                        raise HTTPException(
                            status_code=404,
                            detail=f"File not found: {file_path}"
                        )
                    else:
                        error_data = await response.json()
                        raise HTTPException(
                            status_code=response.status,
                            detail=error_data.get('detail', 'Failed to initiate download')
                        )
                        
        except Exception as e:
            self.logger.error(f"File download failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Storage service error: {str(e)}"
            )

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage
        """
        endpoint = f"{self.base_url}/v1/storage/delete"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json={"path": file_path},
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        return True
                    elif response.status == 404:
                        raise HTTPException(
                            status_code=404,
                            detail=f"File not found: {file_path}"
                        )
                    else:
                        error_data = await response.json()
                        raise HTTPException(
                            status_code=response.status,
                            detail=error_data.get('detail', 'Delete failed')
                        )
                        
        except Exception as e:
            self.logger.error(f"File deletion failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Storage service error: {str(e)}"
            )

    async def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata for a file
        """
        endpoint = f"{self.base_url}/v1/storage/metadata"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    endpoint,
                    params={"path": file_path},
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        raise HTTPException(
                            status_code=404,
                            detail=f"File not found: {file_path}"
                        )
                    else:
                        error_data = await response.json()
                        raise HTTPException(
                            status_code=response.status,
                            detail=error_data.get('detail', 'Failed to get metadata')
                        )
        except Exception as e:
            self.logger.error(f"Failed to get file metadata: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Storage service error: {str(e)}"
            )

    async def list_files(
        self,
        prefix: Optional[str] = None,
        limit: int = 100,
        continuation_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List files in storage with pagination
        """
        endpoint = f"{self.base_url}/v1/storage/list"
        
        params = {
            "limit": limit
        }
        if prefix:
            params["prefix"] = prefix
        if continuation_token:
            params["continuation_token"] = continuation_token

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    endpoint,
                    params=params,
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_data = await response.json()
                        raise HTTPException(
                            status_code=response.status,
                            detail=error_data.get('detail', 'Failed to list files')
                        )
        except Exception as e:
            self.logger.error(f"Failed to list files: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Storage service error: {str(e)}"
            )

    async def generate_presigned_url(
        self,
        file_path: str,
        expiration: int = 3600,
        http_method: str = "GET"
    ) -> str:
        """
        Generate a presigned URL for file access
        """
        endpoint = f"{self.base_url}/v1/storage/presigned"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json={
                        "path": file_path,
                        "expiration": expiration,
                        "http_method": http_method
                    },
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["url"]
                    elif response.status == 404:
                        raise HTTPException(
                            status_code=404,
                            detail=f"File not found: {file_path}"
                        )
                    else:
                        error_data = await response.json()
                        raise HTTPException(
                            status_code=response.status,
                            detail=error_data.get('detail', 'Failed to generate presigned URL')
                        )
        except Exception as e:
            self.logger.error(f"Failed to generate presigned URL: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Storage service error: {str(e)}"
            )