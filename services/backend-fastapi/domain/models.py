from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime

class SummarizationRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Text to summarize")
    model_name: Optional[str] = Field(None, description="Name of the model to use")
    max_length: Optional[int] = Field(300, gt=0, le=1000)
    min_length: Optional[int] = Field(100, gt=0, le=500)
    num_beams: Optional[int] = Field(4, gt=0, le=8)
    length_penalty: Optional[float] = Field(2.0, ge=0.0, le=5.0)
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        return v.strip()

class SummaryResponse(BaseModel):
    summary: str = Field(..., description="Generated summary text")
    original_length: int = Field(..., description="Length of original text")
    summary_length: int = Field(..., description="Length of generated summary")
    model_used: str = Field(..., description="Name of the model used")
    processing_time: float = Field(..., description="Time taken to generate summary in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict] = Field(default_factory=dict)

class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Health status")
    details: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="API version")
    
class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error description")
    error_code: Optional[str] = Field(None, description="Error code for client reference")
    timestamp: datetime = Field(default_factory=datetime.utcnow)