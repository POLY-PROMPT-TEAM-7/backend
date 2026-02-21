"""Parse AWS Textract BLOCKS into structured Document objects."""

from typing import List, Dict, Any
from lib.document_processor.models import Line, Page, Document


class DocumentParser:
    """Parser for AWS Textract BLOCKS response."""

    def __init__(self, textract_blocks: List[Dict[str, Any]]):
        """Initialize parser with Textract BLOCKS.

        Args:
            textract_blocks: List of BLOCK objects from Textract response
        """
        self.blocks = textract_blocks
        self._pages_by_number: Dict[int, List[Dict[str, Any]]] = {}
        self._build_page_map()

    def _build_page_map(self) -> None:
        """Build mapping of page_number to list of LINE blocks."""
        for block in self.blocks:
            if block.get("BlockType") == "PAGE":
                page_num = block.get("Page", 1)
                self._pages_by_number[page_num] = []

            if block.get("BlockType") == "LINE":
                page_num = block.get("Page", 1)
                if page_num not in self._pages_by_number:
                    self._pages_by_number[page_num] = []
                self._pages_by_number[page_num].append(block)

    def parse(self) -> Document:
        """Parse BLOCKS into structured Document object.

        Returns:
            Document with pages, lines, and metadata
        """
        import time
        import uuid
        from datetime import datetime, timezone

        start_time = time.time()

        pages: List[Page] = []
        for page_num in sorted(self._pages_by_number.keys()):
            line_blocks = sorted(
                self._pages_by_number[page_num],
                key=lambda b: b.get("Id", "")
            )
            lines = self._parse_lines(line_blocks)
            page_text = self._build_page_text(lines)
            pages.append(
                Page(page_number=page_num, text=page_text, lines=lines)
            )

        processing_time_ms = int((time.time() - start_time) * 1000)

        return Document(
            pages=pages,
            processing_time_ms=processing_time_ms,
            document_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
        )

    def _parse_lines(self, line_blocks: List[Dict[str, Any]]) -> List[Line]:
        """Parse LINE blocks into Line objects.

        Args:
            line_blocks: List of LINE BLOCK dictionaries

        Returns:
            List of Line objects with line_number, text, confidence
        """
        lines: List[Line] = []
        for idx, block in enumerate(line_blocks, start=1):
            text = block.get("Text", "")
            confidence_raw = block.get("Confidence", 0)
            confidence = float(confidence_raw) / 100.0

            lines.append(
                Line(line_number=idx, text=text, confidence=confidence)
            )
        return lines

    def _build_page_text(self, lines: List[Line]) -> str:
        """Build full page text from line objects.

        Args:
            lines: List of Line objects

        Returns:
            Concatenated text with newlines
        """
        return "\n".join([line.text for line in lines])
