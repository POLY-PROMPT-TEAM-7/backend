import time
import uuid
from datetime import datetime, timezone
from typing import Any
from document_processor.models import Line, Page, Document

class DocumentParser:

  def __init__(self, textract_blocks: list[dict[str, Any]]) -> None:
    self.blocks = textract_blocks
    self._pages_by_number: dict[int, list[dict[str, Any]]] = {}
    self._build_page_map()

  def _build_page_map(self) -> None:
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
    start_time = time.time()
    pages: list[Page] = []
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
      document_id=uuid.uuid4(),
      created_at=datetime.now(timezone.utc),
    )

  def _parse_lines(self, line_blocks: list[dict[str, Any]]) -> list[Line]:
    lines: list[Line] = []
    for idx, block in enumerate(line_blocks, start=1):
      text = block.get("Text", "")
      confidence_raw = block.get("Confidence", 0)
      confidence = float(confidence_raw) / 100.0
      lines.append(
        Line(line_number=idx, text=text, confidence=confidence)
      )
    return lines

  def _build_page_text(self, lines: list[Line]) -> str:
    return "\n".join([line.text for line in lines])
