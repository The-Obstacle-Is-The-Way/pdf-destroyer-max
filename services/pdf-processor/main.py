from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pathlib import Path
import asyncio
from typing import Dict, Optional
import uuid
from datetime import datetime
import aiofiles
from loguru import logger

# Import settings
from config.settings import settings as project_settings
from config.settings import PDFProcessorSettings
service_settings = PDFProcessorSettings()

# Import our components
from text_extractor import PDFTextExtractor
from text_chunker import TextChunker
from ocr_fallback import OCRProcessor
from models import ProcessingResult, ProcessingStatus, ProcessingRequest

# Configure logging based on environment
log_path = service_settings.base_dir / "logs" / "pdf_processor.log"
logger.add(log_path, 
    rotation="500 MB",
    level="DEBUG" if service_settings.debug else "INFO",
    format="{time} {level} {message}")

app = FastAPI(
    title="PDF Processor Service",
    version="1.0.0",
    docs_url=None if project_settings.security['api_key_required'] else "/docs"
)

# Add CORS middleware with settings from config
app.add_middleware(
    CORSMiddleware,
    allow_origins=project_settings.security['allowed_origins'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components with settings
text_extractor = PDFTextExtractor(
    min_text_length=service_settings.min_text_length
)

text_chunker = TextChunker(
    max_chunk_size=service_settings.chunk_size,
    min_chunk_size=service_settings.chunk_size // 10,
    overlap=50
)

ocr_processor = OCRProcessor(
    lang=service_settings.tesseract_language,
    dpi=service_settings.image_quality,
    enhance_image=True
)

# Store processing status
processing_tasks: Dict[str, ProcessingStatus] = {}

class ProcessingOrchestrator:
    def __init__(self):
        self.upload_dir = service_settings.upload_dir
        self.results_dir = service_settings.processed_dir
        self.failed_dir = service_settings.failed_dir
        
        # Ensure directories exist
        for dir_path in [self.upload_dir, self.results_dir, self.failed_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    async def process_pdf(self, task_id: str, file_path: Path):
        """Orchestrates the PDF processing pipeline."""
        try:
            processing_tasks[task_id].status = "PROCESSING"
            logger.info(f"Starting processing for task {task_id}")
            
            # Extract text and images
            extraction_result = await text_extractor.extract_text(str(file_path))
            
            # Identify pages needing OCR
            ocr_pages = [
                page_num for page_num, content in extraction_result.items()
                if content['needs_ocr']
            ]
            
            # Process OCR in parallel if needed
            if ocr_pages:
                logger.info(f"Running OCR for {len(ocr_pages)} pages in task {task_id}")
                ocr_results = await ocr_processor.process_pages(str(file_path), ocr_pages)
                # Merge OCR results back into extraction_result
                for page_num, ocr_text in ocr_results.items():
                    extraction_result[page_num]['text'] = ocr_text
            
            # Chunk the extracted text
            all_chunks = await text_chunker.chunk_document(extraction_result)
            
            # Save results
            result = ProcessingResult(
                task_id=task_id,
                timestamp=datetime.utcnow(),
                page_count=len(extraction_result),
                chunk_count=len(all_chunks),
                ocr_used=bool(ocr_pages),
                content=extraction_result
            )
            
            await self.save_result(task_id, result)
            processing_tasks[task_id].status = "COMPLETED"
            processing_tasks[task_id].result = result
            logger.info(f"Completed processing for task {task_id}")
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {str(e)}")
            processing_tasks[task_id].status = "FAILED"
            processing_tasks[task_id].error = str(e)
            # Move to failed directory
            failed_path = self.failed_dir / file_path.name
            file_path.rename(failed_path)

    async def save_result(self, task_id: str, result: ProcessingResult):
        """Saves processing results to disk."""
        result_path = self.results_dir / f"{task_id}.json"
        async with aiofiles.open(result_path, 'w') as f:
            await f.write(result.json())

orchestrator = ProcessingOrchestrator()

@app.post("/process")
async def process_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    processing_options: Optional[Dict] = None
):
    """
    Process a PDF file and extract its contents.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Check file size
    file_size = 0
    content = await file.read()
    file_size = len(content)
    if file_size > service_settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {service_settings.max_file_size // (1024*1024)}MB"
        )
    
    task_id = str(uuid.uuid4())
    file_path = orchestrator.upload_dir / f"{task_id}.pdf"
    
    try:
        # Save uploaded file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Initialize processing status
        processing_tasks[task_id] = ProcessingStatus(
            task_id=task_id,
            filename=file.filename,
            status="QUEUED",
            timestamp=datetime.utcnow()
        )
        
        # Start processing in background
        background_tasks.add_task(
            orchestrator.process_pdf,
            task_id,
            file_path
        )
        
        return JSONResponse({
            "task_id": task_id,
            "status": "QUEUED",
            "message": "PDF processing started"
        })
        
    except Exception as e:
        logger.error(f"Error initiating PDF processing: {str(e)}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    """Get the status of a processing task."""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return processing_tasks[task_id]

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    """Get the results of a completed processing task."""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    status = processing_tasks[task_id]
    if status.status != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail=f"Task is not completed. Current status: {status.status}"
        )
    
    return status.result

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=service_settings.host,
        port=service_settings.port,
        log_level="debug" if service_settings.debug else "info"
    )