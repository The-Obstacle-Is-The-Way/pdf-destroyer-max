# services/ai-powerhouse-pipelines/tests/test_neural_merger.py

import pytest
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import asyncio

# Import the components we want to test
from src.models.neural_merger.merger import NeuralMerger, TextSegment

class MockProcessorType(Enum):
    TEXT_EXTRACTION = "text_extraction"
    OCR = "ocr"
    LAYOUT_ANALYSIS = "layout_analysis"

@dataclass
class MockProcessingResult:
    processor_type: MockProcessorType
    text_content: str
    confidence_score: float
    metadata: Dict[str, Any]
    page_number: int
    bounding_boxes: List[Dict[str, float]] = None

@pytest.fixture
def neural_merger():
    """Create a NeuralMerger instance for testing"""
    return NeuralMerger()

@pytest.mark.asyncio
async def test_merge_single_result():
    """Test merging a single result (should return it unchanged)"""
    merger = NeuralMerger()
    
    single_result = MockProcessingResult(
        processor_type=MockProcessorType.TEXT_EXTRACTION,
        text_content="This is a test document.",
        confidence_score=0.9,
        metadata={"source": "test"},
        page_number=1
    )
    
    merged = await merger.merge_results([single_result])
    assert merged.text_content == single_result.text_content
    assert merged.confidence_score == single_result.confidence_score

@pytest.mark.asyncio
async def test_merge_overlapping_text():
    """Test merging results with overlapping text"""
    merger = NeuralMerger()
    
    result1 = MockProcessingResult(
        processor_type=MockProcessorType.TEXT_EXTRACTION,
        text_content="This is a test document.",
        confidence_score=0.9,
        metadata={"source": "text_extraction"},
        page_number=1
    )
    
    result2 = MockProcessingResult(
        processor_type=MockProcessorType.OCR,
        text_content="This is a test docment.",  # Slight OCR error
        confidence_score=0.7,
        metadata={"source": "ocr"},
        page_number=1
    )
    
    merged = await merger.merge_results([result1, result2])
    assert merged.text_content == "This is a test document."
    assert merged.confidence_score > 0.7  # Should favor the higher confidence result

@pytest.mark.asyncio
async def test_merge_complementary_text():
    """Test merging results with complementary text"""
    merger = NeuralMerger()
    
    result1 = MockProcessingResult(
        processor_type=MockProcessorType.TEXT_EXTRACTION,
        text_content="First part of text.",
        confidence_score=0.9,
        metadata={"source": "text_extraction"},
        page_number=1,
        bounding_boxes=[{"x": 0, "y": 0, "width": 100, "height": 50}]
    )
    
    result2 = MockProcessingResult(
        processor_type=MockProcessorType.OCR,
        text_content="Second part of text.",
        confidence_score=0.8,
        metadata={"source": "ocr"},
        page_number=1,
        bounding_boxes=[{"x": 0, "y": 50, "width": 100, "height": 50}]
    )
    
    merged = await merger.merge_results([result1, result2])
    assert "First part" in merged.text_content
    assert "Second part" in merged.text_content

@pytest.mark.asyncio
async def test_merge_with_bounding_boxes():
    """Test merging results with overlapping bounding boxes"""
    merger = NeuralMerger()
    
    result1 = MockProcessingResult(
        processor_type=MockProcessorType.TEXT_EXTRACTION,
        text_content="Text block A",
        confidence_score=0.9,
        metadata={},
        page_number=1,
        bounding_boxes=[{"x": 10, "y": 10, "width": 100, "height": 50}]
    )
    
    result2 = MockProcessingResult(
        processor_type=MockProcessorType.OCR,
        text_content="Text block A slightly different",
        confidence_score=0.8,
        metadata={},
        page_number=1,
        bounding_boxes=[{"x": 12, "y": 11, "width": 98, "height": 48}]
    )
    
    merged = await merger.merge_results([result1, result2])
    assert len(merged.bounding_boxes) == 1  # Should merge overlapping boxes
    assert 8 <= merged.bounding_boxes[0]["x"] <= 12  # Should average the coordinates

@pytest.mark.asyncio
async def test_merge_low_confidence_results():
    """Test merging results with low confidence scores"""
    merger = NeuralMerger()
    
    result1 = MockProcessingResult(
        processor_type=MockProcessorType.TEXT_EXTRACTION,
        text_content="Low quality text.",
        confidence_score=0.3,  # Below default threshold
        metadata={},
        page_number=1
    )
    
    result2 = MockProcessingResult(
        processor_type=MockProcessorType.OCR,
        text_content="Also low quality.",
        confidence_score=0.2,  # Below default threshold
        metadata={},
        page_number=1
    )
    
    merged = await merger.merge_results([result1, result2])
    assert merged is None  # Should return None when all results are below threshold

@pytest.mark.asyncio
async def test_merge_metadata():
    """Test merging metadata from multiple results"""
    merger = NeuralMerger()
    
    result1 = MockProcessingResult(
        processor_type=MockProcessorType.TEXT_EXTRACTION,
        text_content="Text 1",
        confidence_score=0.9,
        metadata={"key1": "value1", "shared_key": "value_a"},
        page_number=1
    )
    
    result2 = MockProcessingResult(
        processor_type=MockProcessorType.OCR,
        text_content="Text 2",
        confidence_score=0.8,
        metadata={"key2": "value2", "shared_key": "value_b"},
        page_number=1
    )
    
    merged = await merger.merge_results([result1, result2])
    assert "key1" in merged.metadata
    assert "key2" in merged.metadata
    assert "shared_key" in merged.metadata

@pytest.mark.asyncio
async def test_merge_empty_results():
    """Test merging empty result list"""
    merger = NeuralMerger()
    merged = await merger.merge_results([])
    assert merged is None

@pytest.mark.asyncio
async def test_merge_with_errors():
    """Test merging with error handling"""
    merger = NeuralMerger()
    
    # Create an invalid result that should trigger error handling
    invalid_result = MockProcessingResult(
        processor_type=MockProcessorType.TEXT_EXTRACTION,
        text_content=None,  # Invalid text content
        confidence_score=0.9,
        metadata={},
        page_number=1
    )
    
    valid_result = MockProcessingResult(
        processor_type=MockProcessorType.OCR,
        text_content="Valid text",
        confidence_score=0.8,
        metadata={},
        page_number=1
    )
    
    # Should handle the error and still merge valid result
    merged = await merger.merge_results([invalid_result, valid_result])
    assert merged is not None
    assert merged.text_content == "Valid text"

@pytest.mark.asyncio
async def test_merge_different_lengths():
    """Test merging text segments of different lengths"""
    merger = NeuralMerger()
    
    result1 = MockProcessingResult(
        processor_type=MockProcessorType.TEXT_EXTRACTION,
        text_content="Short text.",
        confidence_score=0.9,
        metadata={},
        page_number=1
    )
    
    result2 = MockProcessingResult(
        processor_type=MockProcessorType.OCR,
        text_content="This is a much longer piece of text that contains more information.",
        confidence_score=0.8,
        metadata={},
        page_number=1
    )
    
    merged = await merger.merge_results([result1, result2])
    assert len(merged.text_content) >= len(result1.text_content)
    assert "more information" in merged.text_content

@pytest.mark.asyncio
async def test_merge_special_characters():
    """Test merging text with special characters"""
    merger = NeuralMerger()
    
    result1 = MockProcessingResult(
        processor_type=MockProcessorType.TEXT_EXTRACTION,
        text_content="Text with symbols: @#$%",
        confidence_score=0.9,
        metadata={},
        page_number=1
    )
    
    result2 = MockProcessingResult(
        processor_type=MockProcessorType.OCR,
        text_content="Text with unicode: 你好",
        confidence_score=0.8,
        metadata={},
        page_number=1
    )
    
    merged = await merger.merge_results([result1, result2])
    assert "@#$%" in merged.text_content
    assert "你好" in merged.text_content