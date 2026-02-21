"""Tests for DocumentParser."""

import pytest
from lib.document_processor.parser import DocumentParser
from lib.document_processor.models import Line, Page, Document


def test_parser_creation():
    """Parser should initialize with Textract BLOCKS."""
    blocks = [
        {"BlockType": "PAGE", "Page": 1},
        {"BlockType": "LINE", "Text": "Test line", "Confidence": 95.5, "Page": 1},
    ]
    parser = DocumentParser(blocks)
    assert len(parser._pages_by_number) == 1
    assert 1 in parser._pages_by_number


def test_parse_single_page():
    """Parser should parse single page with one line."""
    blocks = [
        {"BlockType": "PAGE", "Page": 1},
        {"BlockType": "LINE", "Text": "Hello World", "Confidence": 98.0, "Page": 1},
    ]
    parser = DocumentParser(blocks)
    doc = parser.parse()

    assert len(doc.pages) == 1
    assert doc.pages[0].page_number == 1
    assert doc.pages[0].text == "Hello World"
    assert len(doc.pages[0].lines) == 1
    assert doc.pages[0].lines[0].text == "Hello World"
    assert doc.pages[0].lines[0].confidence == 0.98


def test_parse_multiple_pages():
    """Parser should parse multiple pages with lines."""
    blocks = [
        {"BlockType": "PAGE", "Page": 1},
        {"BlockType": "LINE", "Text": "Page 1 Line 1", "Confidence": 95.0, "Page": 1},
        {"BlockType": "LINE", "Text": "Page 1 Line 2", "Confidence": 97.0, "Page": 1},
        {"BlockType": "PAGE", "Page": 2},
        {"BlockType": "LINE", "Text": "Page 2 Line 1", "Confidence": 96.0, "Page": 2},
    ]
    parser = DocumentParser(blocks)
    doc = parser.parse()

    assert len(doc.pages) == 2
    assert doc.pages[0].page_number == 1
    assert doc.pages[1].page_number == 2
    assert len(doc.pages[0].lines) == 2
    assert len(doc.pages[1].lines) == 1


def test_confidence_conversion():
    """Parser should convert Textract confidence (0-100) to (0-1)."""
    blocks = [
        {"BlockType": "PAGE", "Page": 1},
        {"BlockType": "LINE", "Text": "Test", "Confidence": 75.0, "Page": 1},
    ]
    parser = DocumentParser(blocks)
    doc = parser.parse()

    assert doc.pages[0].lines[0].confidence == 0.75


def test_line_numbering():
    """Parser should number lines starting from 1."""
    blocks = [
        {"BlockType": "PAGE", "Page": 1},
        {"BlockType": "LINE", "Text": "Line 1", "Confidence": 95.0, "Page": 1},
        {"BlockType": "LINE", "Text": "Line 2", "Confidence": 95.0, "Page": 1},
        {"BlockType": "LINE", "Text": "Line 3", "Confidence": 95.0, "Page": 1},
    ]
    parser = DocumentParser(blocks)
    doc = parser.parse()

    assert doc.pages[0].lines[0].line_number == 1
    assert doc.pages[0].lines[1].line_number == 2
    assert doc.pages[0].lines[2].line_number == 3


def test_page_text_concatenation():
    """Parser should concatenate lines with newlines."""
    blocks = [
        {"BlockType": "PAGE", "Page": 1},
        {"BlockType": "LINE", "Text": "First line", "Confidence": 95.0, "Page": 1},
        {"BlockType": "LINE", "Text": "Second line", "Confidence": 95.0, "Page": 1},
    ]
    parser = DocumentParser(blocks)
    doc = doc = parser.parse()

    assert doc.pages[0].text == "First line\nSecond line"


def test_empty_blocks():
    """Parser should handle empty BLOCKS gracefully."""
    parser = DocumentParser([])
    doc = parser.parse()

    assert len(doc.pages) == 0
    assert doc.processing_time_ms >= 0
    assert doc.document_id is not None
