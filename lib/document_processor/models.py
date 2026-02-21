"""Pydantic models for structured document output."""

from datetime import datetime
from typing import List
import uuid

from pydantic import BaseModel, Field


class Line(BaseModel):
    """A single line of text from a document."""

    line_number: int = Field(..., description="Line number on the page (1-indexed)")
    text: str = Field(..., description="Text content of the line")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="OCR confidence score (0-1)",
    )


class Page(BaseModel):
    """A single page from a document."""

    page_number: int = Field(..., description="Page number (1-indexed)")
    text: str = Field(..., description="Full text content of the page")
    lines: List[Line] = Field(
        default_factory=list,
        description="List of lines on the page",
    )


class Document(BaseModel):
    """Complete structured document with processing metadata."""

    document_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique document identifier",
    )
    pages: List[Page] = Field(..., description="List of pages in the document")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when document was processed",
    )
