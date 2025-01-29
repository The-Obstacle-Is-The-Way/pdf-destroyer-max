# services/backend-fastapi/tests/test_backend_fastapi.py

import pytest
from fastapi.testclient import TestClient
from main import app
import asyncio
from unittest.mock import Mock, patch
import os
import json
from datetime import datetime

client = TestClient(app)

@pytest.fixture
def mock_ocr_service():
    with patch("api.dependencies.OCRService") as mock:
        yield mock

@pytest.fixture
def mock_summarization_service():
    with patch("api.dependencies.SummarizationService") as mock:
        yield mock

@pytest.fixture
def mock_pdf_pipeline():
    with patch("api.dependencies.PDFPipelineService") as mock:
        yield mock

def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "PDF Destroyer Max API is running" in response.json()["message"]

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_pdf_processing(mock_pdf_pipeline):
    """Test PDF processing endpoint"""
    # Create a test PDF file
    test_pdf_content = b"%PDF-1.4 test content"
    with open("test.pdf", "wb") as f:
        f.write(test_pdf_content)

    try:
        with open("test.pdf", "rb") as f:
            response = client.post(
                "/pdf/process",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        
        assert response.status_code == 200
        result = response.json()
        assert "task_id" in result
        assert result["status"] == "QUEUED"

    finally:
        # Cleanup
        if os.path.exists("test.pdf"):
            os.remove("test.pdf")

@pytest.mark.asyncio
async def test_summarization(mock_summarization_service):
    """Test text summarization endpoint"""
    test_text = "This is a test text that needs to be summarized."
    
    # Mock the summarization service response
    mock_summary = {
        "summary": "Test summary",
        "model_used": "test-model",
        "processing_time": 0.5,
        "text_length": len(test_text.split()),
        "summary_length": 2,
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": {}
    }
    
    mock_summarization_service.return_value.summarize_text.return_value = mock_summary

    response = client.post(
        "/api/summarize/",
        json={
            "text": test_text,
            "max_length": 50,
            "min_length": 10
        }
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "summary" in result
    assert result["summary"] == "Test summary"

@pytest.mark.asyncio
async def test_ocr_processing(mock_ocr_service):
    """Test OCR processing endpoint"""
    # Create a test image
    test_image_content = b"fake image content"
    with open("test_image.png", "wb") as f:
        f.write(test_image_content)

    try:
        # Mock OCR service response
        mock_ocr_service.return_value.extract_text.return_value = {
            "text