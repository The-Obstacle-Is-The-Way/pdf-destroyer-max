# main.py
import os, torch
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import numpy as np
import cv2
from text_extraction import EnhancedOCRProcessor

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ocr_processor = EnhancedOCRProcessor()

class OCRResponse(BaseModel):
    text: str
    confidence: float
    processing_time: float
    layout_info: Optional[List[Dict]] = None

@app.get("/health")
async def health_check():
    gpu_available = "cuda" if torch.cuda.is_available() else "cpu"
    return {
        "status": "healthy",
        "service": "ocr-tesseract",
        "gpu": gpu_available
    }

@app.post("/ocr", response_model=OCRResponse)
async def ocr(file: UploadFile = File(...)):
    if not file.content_type.startswith('image/'):
        raise HTTPException(400, "File must be an image")
    
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise HTTPException(400, "Could not decode image")
    
    result = await ocr_processor.extract_text(img)
    
    return OCRResponse(
        text=result.text,
        confidence=result.confidence,
        processing_time=result.processing_time,
        layout_info=result.layout_info
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)