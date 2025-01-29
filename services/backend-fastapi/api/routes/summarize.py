from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from ..summarization_service import SummarizationService, SummarizationRequest, SummaryResponse
from ..dependencies import get_summarization_service
from typing import List, Optional
import asyncio
import logging
from pydantic import constr

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/summarize", tags=["summarization"])

@router.post(
    "/",
    response_model=SummaryResponse,
    summary="Summarize text",
    description="Generate a summary of the provided text using transformers",
    response_description="Generated summary with metadata"
)
async def summarize_text(
    request: SummarizationRequest,
    background_tasks: BackgroundTasks,
    max_length: Optional[int] = Query(300, gt=0, le=1000),
    summarization_service: SummarizationService = Depends(get_summarization_service)
):
    """
    Generate a summary from input text with configurable parameters
    
    - **text**: Input text to summarize
    - **max_length**: Maximum length of generated summary
    - **min_length**: Minimum length of generated summary
    - **model_name**: Name of model to use (optional)
    """
    try:
        request.validate_text()
        return await summarization_service.summarize_text(
            request, 
            background_tasks,
            max_length=max_length
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error in summarize endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Summarization failed")

@router.post(
    "/batch",
    response_model=List[SummaryResponse],
    summary="Batch summarize texts",
    description="Generate summaries for multiple texts in parallel"
)
async def batch_summarize(
    requests: List[SummarizationRequest],
    background_tasks: BackgroundTasks,
    max_batch_size: int = Query(10, gt=0, le=50),
    summarization_service: SummarizationService = Depends(get_summarization_service)
):
    """Process multiple texts in parallel with controlled concurrency"""
    if len(requests) > max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size exceeds maximum allowed ({max_batch_size})"
        )
        
    try:
        tasks = [
            summarization_service.summarize_text(req, background_tasks)
            for req in requests
        ]
        return await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"Error in batch summarize endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Batch summarization failed")

@router.get(
    "/health",
    summary="Check summarization service health",
    description="Verify the summarization service and model are functioning"
)
async def health_check(
    summarization_service: SummarizationService = Depends(get_summarization_service)
):
    """Check health of summarization service and model"""
    try:
        status = await summarization_service.health_check()
        if status["healthy"]:
            return status
        raise HTTPException(
            status_code=503, 
            detail=f"Summarization service unhealthy: {status.get('details')}"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail="Health check failed"
        )