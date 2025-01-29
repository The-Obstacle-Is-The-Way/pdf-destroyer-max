# services/ai-powerhouse-pipelines/tests/test_models/test_quality_scoring.py

import pytest
from typing import Dict, Any
from dataclasses import dataclass
import asyncio

# Import the components we want to test
from src.models.quality_scoring.scorer import QualityScorer, QualityMetrics

# Mock ProcessingResult for testing
@dataclass
class MockProcessingResult:
    text_content: str
    confidence_score: float
    metadata: Dict[str, Any]
    processor_type: str
    page_number: int
    bounding_boxes: list = None

@pytest.fixture
def quality_scorer():
    """Create a QualityScorer instance for testing"""
    return QualityScorer()

@pytest.mark.asyncio
async def test_perfect_text_scoring():
    """Test scoring with well-formatted, coherent text"""
    scorer = QualityScorer()
    perfect_result = MockProcessingResult(
        text_content="This is a well-formatted paragraph. It contains complete sentences. "
                    "The formatting is consistent throughout the text. Each sentence "
                    "starts with a capital letter and ends properly.",
        confidence_score=0.95,
        metadata={},
        processor_type="text_extraction",
        page_number=1
    )
    
    score = await scorer.score_result(perfect_result)
    assert score >= 0.8, "Perfect text should score highly"

@pytest.mark.asyncio
async def test_noisy_text_scoring():
    """Test scoring with noisy, poorly formatted text"""
    scorer = QualityScorer()
    noisy_result = MockProcessingResult(
        text_content="THis  is  POOrly  f0rmatted t3xt... it  has  weird  spacing   and"
                    "numb3rs... som3 w3ird ch@racters!!!",
        confidence_score=0.4,
        metadata={},
        processor_type="ocr",
        page_number=1
    )
    
    score = await scorer.score_result(noisy_result)
    assert score < 0.5, "Noisy text should score poorly"

@pytest.mark.asyncio
async def test_empty_text_scoring():
    """Test scoring with empty text"""
    scorer = QualityScorer()
    empty_result = MockProcessingResult(
        text_content="",
        confidence_score=0.0,
        metadata={},
        processor_type="text_extraction",
        page_number=1
    )
    
    score = await scorer.score_result(empty_result)
    assert score == 0.0, "Empty text should score zero"

@pytest.mark.asyncio
async def test_incomplete_text_scoring():
    """Test scoring with incomplete sentences"""
    scorer = QualityScorer()
    incomplete_result = MockProcessingResult(
        text_content="This sentence is not... The next one also... And then",
        confidence_score=0.6,
        metadata={},
        processor_type="text_extraction",
        page_number=1
    )
    
    score = await scorer.score_result(incomplete_result)
    assert 0.3 <= score <= 0.7, "Incomplete text should score in middle range"

@pytest.mark.asyncio
async def test_formatting_consistency():
    """Test scoring text with inconsistent formatting"""
    scorer = QualityScorer()
    inconsistent_result = MockProcessingResult(
        text_content="Normal sentence here.\n"
                    "    SUDDENLY ALL CAPS!\n"
                    "back to normal...\n"
                    "   Weird     spacing    here",
        confidence_score=0.7,
        metadata={},
        processor_type="text_extraction",
        page_number=1
    )
    
    metrics = await scorer._calculate_metrics(inconsistent_result)
    assert metrics.formatting_consistency < 0.7, "Inconsistent formatting should be detected"

@pytest.mark.asyncio
async def test_text_coherence():
    """Test text coherence measurement"""
    scorer = QualityScorer()
    
    # Test with coherent text
    coherent_text = "This is a coherent paragraph. It has proper sentences. They follow logically."
    coherent_result = MockProcessingResult(
        text_content=coherent_text,
        confidence_score=0.9,
        metadata={},
        processor_type="text_extraction",
        page_number=1
    )
    
    metrics = await scorer._calculate_metrics(coherent_result)
    assert metrics.text_coherence > 0.7, "Coherent text should have high coherence score"

@pytest.mark.asyncio
async def test_noise_detection():
    """Test noise level detection"""
    scorer = QualityScorer()
    
    # Test with noisy text
    noisy_text = "Th1s h@s l0ts 0f n0ise!!! $$$ ### @@@ ^^^ </noise>"
    noisy_result = MockProcessingResult(
        text_content=noisy_text,
        confidence_score=0.3,
        metadata={},
        processor_type="ocr",
        page_number=1
    )
    
    metrics = await scorer._calculate_metrics(noisy_result)
    assert metrics.noise_level > 0.7, "Noisy text should have high noise level"

@pytest.mark.asyncio
async def test_completeness_measurement():
    """Test completeness measurement"""
    scorer = QualityScorer()
    
    # Test with incomplete text
    incomplete_text = "This sentence never... And this one is cut-"
    incomplete_result = MockProcessingResult(
        text_content=incomplete_text,
        confidence_score=0.5,
        metadata={},
        processor_type="text_extraction",
        page_number=1
    )
    
    metrics = await scorer._calculate_metrics(incomplete_result)
    assert metrics.completeness < 0.5, "Incomplete text should have low completeness score"

@pytest.mark.asyncio
async def test_edge_cases():
    """Test various edge cases"""
    scorer = QualityScorer()
    
    # Test with very long text
    long_text = "Normal sentence. " * 1000
    long_result = MockProcessingResult(
        text_content=long_text,
        confidence_score=0.8,
        metadata={},
        processor_type="text_extraction",
        page_number=1
    )
    
    score = await scorer.score_result(long_result)
    assert 0.0 <= score <= 1.0, "Score should be normalized between 0 and 1"
    
    # Test with special characters
    special_chars = "🌟 Unicode text with emojis 🌈 and symbols ™®©"
    special_result = MockProcessingResult(
        text_content=special_chars,
        confidence_score=0.7,
        metadata={},
        processor_type="text_extraction",
        page_number=1
    )
    
    score = await scorer.score_result(special_result)
    assert 0.0 <= score <= 1.0, "Should handle special characters gracefully"