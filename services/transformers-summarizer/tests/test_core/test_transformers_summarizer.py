import pytest
from unittest.mock import patch
from transformers import pipeline
from summarization_service import TransformerService
from fastapi.testclient import TestClient
from main import app
import os
import torch
import requests

# Test: Summarization success
def test_summarize_text_success():
    # Arrange
    transformer_service = TransformerService()
    test_text = "This is a sample text to summarize."
    mock_summary = [{"summary_text": "This is a summary."}]

    # Act
    with patch.object(pipeline, '__call__', return_value=mock_summary):
        summary = transformer_service.summarize_text(test_text)

    # Assert
    assert summary == "This is a summary."

# Test: Summarization failure (empty input)
def test_summarize_text_empty_input():
    # Arrange
    transformer_service = TransformerService()
    test_text = ""

    # Act & Assert
    with pytest.raises(ValueError, match="Input text cannot be empty."):
        transformer_service.summarize_text(test_text)

# Test: Summarization with different parameters
def test_summarize_text_with_parameters():
    # Arrange
    transformer_service = TransformerService()
    test_text = "This is another sample text that needs to be summarized."
    mock_summary = [{"summary_text": "Another summary."}]

    # Act
    with patch.object(pipeline, '__call__', return_value=mock_summary):
        summary = transformer_service.summarize_text(test_text, max_length=50, min_length=20, do_sample=True)

    # Assert
    assert summary == "Another summary."

# Test: Summarization service health check
def test_service_health_check():
    # Arrange
    app = TransformerService()

    # Act
    health_response = app.health_check()

    # Assert
    assert health_response == {"status": "healthy", "service": "transformers-summarizer"}

# Test: GPU Availability
def test_gpu_availability():
    # Arrange
    use_gpu = os.getenv("USE_GPU", "false").lower() == "true"
    gpu_available = torch.cuda.is_available()

    # Act
    if use_gpu:
        assert gpu_available, "GPU is requested but not available."
    else:
        assert not use_gpu or not gpu_available, "GPU not requested or not available."

# Test: OCR Integration
def test_ocr_integration():
    # Arrange
    transformer_service = TransformerService()
    test_image_path = "dummy_image_path.jpg"
    mock_extracted_text = "This is the extracted text from OCR."
    mock_summary = [{"summary_text": "This is a summary of the OCR text."}]

    # Mock the OCR extraction and summarization steps
    with patch("summarization_service.extract_text_from_image", return_value=mock_extracted_text):
        with patch.object(pipeline, '__call__', return_value=mock_summary):
            # Act
            summary = transformer_service.ocr_summarize(test_image_path)

    # Assert
    assert summary == "This is a summary of the OCR text."

# Test: OCR and Summarization Integration
def test_ocr_summarization_integration():
    # Arrange
    client = TestClient(app)
    test_image_path = "sample_image_path.jpg"
    ocr_mock_response = "Extracted text from OCR."
    summarization_mock_response = [{"summary_text": "This is a summarized version of the extracted text."}]

    # Mock OCR service response
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"extracted_text": ocr_mock_response}

        # Mock Summarization response
        with patch.object(pipeline, '__call__', return_value=summarization_mock_response):
            response = client.post("/ocr-summarize", json={"image_path": test_image_path})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"summary": "This is a summarized version of the extracted text."}

# Test: OCR Failure
def test_ocr_service_failure():
    # Arrange
    client = TestClient(app)
    test_image_path = "non_existent_image.jpg"

    # Mock OCR service failure
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 500
        mock_post.return_value.raise_for_status.side_effect = requests.exceptions.RequestException("OCR service error")

        # Act
        response = client.post("/ocr-summarize", json={"image_path": test_image_path})

    # Assert
    assert response.status_code == 500
    assert response.json() == {"detail": "OCR service error: OCR service error"}

# Test: Summarization Endpoint (Direct API test)
def test_api_summarize_endpoint():
    # Arrange
    client = TestClient(app)
    test_text = "This is a sample text for the summarize endpoint."
    summarization_mock_response = [{"summary_text": "This is a summarized version."}]

    # Mock Summarization response
    with patch.object(pipeline, '__call__', return_value=summarization_mock_response):
        response = client.post("/summarize", json={"text": test_text, "max_length": 100, "min_length": 20, "do_sample": False})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"summary": "This is a summarized version."}

# Test: Health Check Endpoint
def test_api_health_check():
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/health")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "transformers-summarizer"}
