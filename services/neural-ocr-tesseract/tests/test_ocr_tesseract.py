import pytest
import cv2
import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from main import app
from text_extraction import EnhancedOCRProcessor

client = TestClient(app)

@pytest.fixture
def sample_image():
    """Create a sample image with text for testing"""
    img = np.zeros((100, 300), dtype=np.uint8)
    img.fill(255)
    # Add black text
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, 'Test OCR', (10, 50), font, 1, (0, 0, 0), 2)
    return img

@pytest.fixture
def ocr_processor():
    """Create an OCR processor instance"""
    return EnhancedOCRProcessor()

def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "ocr-tesseract"}

@pytest.mark.asyncio
async def test_preprocess_image(ocr_processor, sample_image):
    """Test image preprocessing"""
    processed = await ocr_processor.preprocess_image(sample_image)
    assert processed is not None
    assert isinstance(processed, np.ndarray)
    assert len(processed.shape) == 2  # Should be grayscale

@pytest.mark.asyncio
async def test_extract_text(ocr_processor, sample_image):
    """Test text extraction"""
    result = await ocr_processor.extract_text(sample_image)
    assert result.text is not None
    assert result.confidence >= 0.0
    assert result.language == "eng"
    assert len(result.bounding_boxes) > 0
    assert result.processing_time > 0.0

def test_ocr_endpoint_with_image(sample_image):
    """Test the OCR endpoint with an image"""
    # Save sample image to bytes
    success, buffer = cv2.imencode(".png", sample_image)
    assert success
    
    # Create test file
    files = {"file": ("test.png", buffer.tobytes(), "image/png")}
    response = client.post("/ocr", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert "text" in data
    assert "confidence" in data
    assert "bounding_boxes" in data
    assert "proces
