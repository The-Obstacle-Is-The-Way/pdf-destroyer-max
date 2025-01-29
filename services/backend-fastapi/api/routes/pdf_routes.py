# services/backend-fastapi/api/routes/pdf.py

import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from ..clients.pipeline_client import get_pipeline_client, PipelineClient, PipelineError
from typing import Dict, Any
from loguru import logger
from ..dependencies import get_current_user  # If you have auth
from ...domain.models import ProcessingResult

# Create router instance
router = APIRouter(
    prefix="/api/v1/pdf",
    tags=["pdf"],
    responses={404: {"description": "Not found"}},
)

@router.post("/process", response_model=ProcessingResult)
async def process_document(
    file: UploadFile = File(...),
    pipeline_client: PipelineClient = Depends(get_pipeline_client),
    # current_user: User = Depends(get_current_user)  # Uncomment if using auth
):
    """
    Process a PDF document through the AI pipeline
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, 
            detail="File must be a PDF"
        )
        
    try:
        # Read file content
        content = await file.read()
        task_id = str(uuid.uuid4())
        
        logger.info(f"Starting processing of file {file.filename} with task ID {task_id}")
        
        # Process through pipeline
        result = await pipeline_client.process_document(
            document_data=content,
            task_id=task_id,
            file_name=file.filename
        )
        
        logger.info(f"Successfully processed file {file.filename}")
        return result
        
    except PipelineError as e:
        logger.error(f"Pipeline error processing {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline processing error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error processing {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during processing"
        )

@router.get("/status/{task_id}", response_model=Dict[str, Any])
async def get_processing_status(
    task_id: str,
    pipeline_client: PipelineClient = Depends(get_pipeline_client),
    # current_user: User = Depends(get_current_user)  # Uncomment if using auth
):
    """
    Get the status of a PDF processing task
    """
    try:
        status = await pipeline_client.get_task_status(task_id)
        return status
    except PipelineError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking task status: {str(e)}"
        )

@router.get("/health", response_model=Dict[str, Any])
async def check_pipeline_health(
    pipeline_client: PipelineClient = Depends(get_pipeline_client)
):
    """
    Check health of the PDF processing pipeline
    """
    return await pipeline_client.get_service_health()