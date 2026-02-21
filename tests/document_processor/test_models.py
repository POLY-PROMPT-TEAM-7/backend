"""Tests for document processor models."""

import uuid

import pytest

from lib.document_processor.models import Document, Line, Page


def test_line_creation():
    """Line model should create with valid data."""
    line = Line(line_number=1, text="Test line", confidence=0.95)
    assert line.line_number == 1
    assert line.text == "Test line"
    assert line.confidence == 0.95


def test_line_confidence_validation():
    """Line should reject confidence outside 0-1 range."""
    with pytest.raises(ValueError):
        Line(line_number=1, text="Test", confidence=1.5)

    with pytest.raises(ValueError):
        Line(line_number=1, text="Test", confidence=-0.1)


def test_page_creation():
    """Page model should create with valid data."""
    lines = [Line(line_number=1, text="Line 1", confidence=0.95)]
    page = Page(page_number=1, text="Page text", lines=lines)
    assert page.page_number == 1
    assert page.text == "Page text"
    assert len(page.lines) == 1
    assert page.lines[0].text == "Line 1"


def test_page_default_lines():
    """Page should default to empty lines list."""
    page = Page(page_number=1, text="Page text")
    assert page.lines == []


def test_document_creation():
    """Document model should create with valid data."""
    pages = [
        Page(
            page_number=1,
            text="Page 1",
            lines=[Line(line_number=1, text="Line 1", confidence=0.95)],
        )
    ]
    doc = Document(pages=pages, processing_time_ms=1000)
    assert doc.document_id is not None
    assert len(doc.pages) == 1
    assert doc.processing_time_ms == 1000


def test_document_default_id():
    """Document should generate UUID by default."""
    doc = Document(pages=[], processing_time_ms=100)
    assert isinstance(doc.document_id, uuid.UUID)
