from typing import List, Optional, Dict, Any
import httpx
import asyncio
from pydantic import BaseModel, Field, validator
from fastapi import HTTPException, BackgroundTasks
import logging
from utils.helpers import async_retry  # Changed to absolute import
import os
from datetime import datetime
from config.settings import Settings

logger = logging.getLogger(__name__)

class SummarizationRequest(BaseModel):
    """Request model for summarization"""
    text: str = Field(..., description="Text to summarize")
    max_length: Optional[int] = Field(130, ge=1, le=1000, description="Maximum length of generated summary")
    min_length: Optional[int] = Field(30, ge=1, description="Minimum length of generated summary")
    do_sample: Optional[bool] = Field(False, description="Whether to use sampling in generation")
    model_name: Optional[str] = Field("facebook/bart-large-cnn", description="Model to use for summarization")
    num_beams: Optional[int] = Field(4, ge=1, le=8, description="Number of beams for beam search")
    length_penalty: Optional[float] = Field(2.0, ge=0.0, le=5.0, description="Length penalty")

    @validator('text')
    def text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Text cannot be empty')
        return v.strip()

class SummaryResponse(BaseModel):
    """Response model for summarization"""
    summary: str
    model_used: str
    processing_time: float
    text_length: int
    summary_length: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SummarizationService:
    """Service for text summarization with chunking support"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.transformer_url = settings.transformer_service_url
        self.timeout = httpx.Timeout(settings.transformer_timeout)
        self.max_retries = settings.max_retries
        self.chunk_size = 1024
        self.max_parallel_requests = 3
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Create and configure HTTP client with connection pooling"""
        return httpx.AsyncClient(
            base_url=self.transformer_url,
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            http2=True
        )

    def _chunk_text(self, text: str, chunk_size: int = 1024) -> List[str]:
        """Split text into chunks of roughly equal size, preserving sentence boundaries"""
        # Simple sentence splitting - can be improved with nltk or spacy
        sentences = text.replace('! ', '!|').replace('? ', '?|').replace('. ', '.|').split('|')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence.split())
            if current_size + sentence_size > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
                
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks

    @retry_async(max_retries=3, delay=1)
    async def _process_chunk(self, chunk: str, client: httpx.AsyncClient, params: Dict) -> str:
        """Process a single chunk of text with retries"""
        try:
            start_time = datetime.utcnow()
            response = await client.post(
                "/generate",
                json={
                    "inputs": chunk,
                    "parameters": {
                        "max_length": params.get('max_length', self.settings.max_length),
                        "min_length": params.get('min_length', self.settings.min_length),
                        "do_sample": params.get('do_sample', False),
                        "num_beams": params.get('num_beams', self.settings.num_beams),
                        "length_penalty": params.get('length_penalty', self.settings.length_penalty),
                        "model_name": params.get('model_name', self.settings.default_model)
                    }
                }
            )
            response.raise_for_status()
            logger.info(f"Chunk processed in {(datetime.utcnow() - start_time).total_seconds():.2f}s")
            return response.json()["summary"]
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error processing chunk: {str(e)}")
            raise HTTPException(status_code=503, detail="Summarization service unavailable")
            
        except Exception as e:
            logger.error(f"Error processing chunk: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def summarize_text(
        self, 
        request: SummarizationRequest,
        background_tasks: BackgroundTasks,
        max_length: Optional[int] = None
    ) -> SummaryResponse:
        """
        Summarize text with support for long documents through chunking
        
        Args:
            request: SummarizationRequest containing text and parameters
            background_tasks: FastAPI BackgroundTasks for cleanup
            max_length: Optional override for max_length parameter
            
        Returns:
            SummaryResponse with generated summary and metadata
        """
        start_time = datetime.utcnow()
        
        try:
            # Update request parameters with any overrides
            request_params = request.dict()
            if max_length:
                request_params['max_length'] = max_length

            async with await self._get_client() as client:
                # For short texts, process directly
                if len(request.text.split()) <= self.chunk_size:
                    summary = await self._process_chunk(request.text, client, request_params)
                
                # For long texts, process in chunks with controlled concurrency
                else:
                    chunks = self._chunk_text(request.text, self.chunk_size)
                    logger.info(f"Processing text in {len(chunks)} chunks")
                    
                    semaphore = asyncio.Semaphore(self.max_parallel_requests)
                    
                    async def process_with_semaphore(chunk: str) -> str:
                        async with semaphore:
                            return await self._process_chunk(chunk, client, request_params)
                    
                    chunk_summaries = await asyncio.gather(
                        *[process_with_semaphore(chunk) for chunk in chunks],
                        return_exceptions=True
                    )
                    
                    # Handle any failed chunks
                    failed_chunks = [i for i, x in enumerate(chunk_summaries) if isinstance(x, Exception)]
                    if failed_chunks:
                        logger.error(f"Failed to process chunks: {failed_chunks}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to process {len(failed_chunks)} chunks"
                        )
                    
                    # Combine chunk summaries and create final summary if needed
                    combined_summary = " ".join(chunk_summaries)
                    if len(combined_summary.split()) > request_params.get('max_length', self.settings.max_length):
                        summary = await self._process_chunk(combined_summary, client, request_params)
                    else:
                        summary = combined_summary

                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Create response with metadata
                response = SummaryResponse(
                    summary=summary,
                    model_used=request_params.get('model_name', self.settings.default_model),
                    processing_time=processing_time,
                    text_length=len(request.text.split()),
                    summary_length=len(summary.split()),
                    metadata={
                        "chunks_processed": len(chunks) if len(request.text.split()) > self.chunk_size else 1,
                        "parameters": request_params,
                        "transformer_service": self.transformer_url
                    }
                )
                
                # Add cleanup task
                background_tasks.add_task(self._cleanup_resources, request.text)
                
                return response

        except asyncio.TimeoutError:
            logger.error("Timeout while connecting to transformer service")
            raise HTTPException(status_code=504, detail="Summarization service timeout")
            
        except Exception as e:
            logger.error(f"Error in summarization service: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def batch_summarize(
        self,
        requests: List[SummarizationRequest],
        background_tasks: BackgroundTasks
    ) -> List[SummaryResponse]:
        """Process multiple summarization requests in parallel"""
        tasks = [
            self.summarize_text(req, background_tasks)
            for req in requests
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def health_check(self) -> Dict:
        """Check if the transformer service is healthy"""
        try:
            async with await self._get_client() as client:
                start_time = datetime.utcnow()
                response = await client.get("/health")
                latency = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                if response.status_code == 200:
                    return {
                        "healthy": True,
                        "details": {
                            "transformer_service": "healthy",
                            "latency_ms": latency,
                            "model_loaded": True
                        }
                    }
                return {
                    "healthy": False,
                    "details": {
                        "transformer_service": "unhealthy",
                        "status_code": response.status_code
                    }
                }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "healthy": False,
                "details": {
                    "transformer_service": "unhealthy",
                    "error": str(e)
                }
            }

    async def _cleanup_resources(self, text: str):
        """Cleanup any temporary resources"""
        try:
            # Implement resource cleanup as needed
            pass
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")

# Don't create a global instance - use dependency injection instead