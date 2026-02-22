import asyncio
import gzip
import importlib
import io
import json
from pathlib import Path
import sys
from typing import Any, cast
from collections.abc import Coroutine
from types import ModuleType
import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile
TEST_DIR = Path(__file__).resolve().parent
GZIP_FIXTURES_DIR = TEST_DIR / "test_files_gzip"
RAW_FIXTURES_DIR = TEST_DIR / "test_files"
@pytest.fixture
def api_module(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> ModuleType:
  project_root = Path(__file__).resolve().parents[2]
  lib_path = str(project_root / "lib")
  sys.path.insert(0, lib_path)
  for module_name in list(sys.modules.keys()):
    if module_name == "document_processor" or module_name.startswith("document_processor."):
      sys.modules.pop(module_name, None)
    if module_name == "backend_placeholder" or module_name.startswith("backend_placeholder."):
      sys.modules.pop(module_name, None)
  imported = importlib.import_module("backend_placeholder.api")
  monkeypatch.chdir(tmp_path)
  return imported

async def _upload(api_module: ModuleType, filename: str, payload: bytes) -> dict[str, Any]:
  upload_file = UploadFile(filename=filename, file=io.BytesIO(payload))
  return await api_module.upload_document(upload_file)

def _run(coro: Coroutine[Any, Any, Any]) -> Any:
  return asyncio.run(coro)

def _assert_success_payload(payload: dict[str, Any]) -> None:
  assert isinstance(payload.get("document_id"), str)
  assert isinstance(payload.get("pages"), list)
  assert isinstance(payload.get("processing_time_ms"), int)
  assert isinstance(payload.get("created_at"), str)

def _assert_saved_json(tmp_path: Path, stem: str) -> dict[str, Any]:
  output_path = tmp_path / "tmp" / f"{stem}.json"
  assert output_path.exists(), f"Expected output file {output_path} to exist"
  saved = json.loads(output_path.read_text(encoding="utf-8"))
  _assert_success_payload(saved)
  return saved
def test_upload_gz_txt_success_and_writes_output(api_module: ModuleType, tmp_path: Path) -> None:
  file_path = GZIP_FIXTURES_DIR / "txtfile.txt.gz"
  payload = _run(_upload(api_module, file_path.name, file_path.read_bytes()))
  _assert_success_payload(payload)
  saved = _assert_saved_json(tmp_path, "txtfile")
  assert saved == payload
def test_upload_gz_docx_success_and_writes_output(
  api_module: ModuleType,
  monkeypatch: pytest.MonkeyPatch,
  tmp_path: Path,
) -> None:
  monkeypatch.setattr(
    api_module,
    "_create_textract_blocks_from_docx",
    lambda _: {
      "Blocks": [
        {"BlockType": "PAGE", "Page": 1, "Id": "page-docx"},
        {
          "BlockType": "LINE",
          "Page": 1,
          "Id": "line-docx",
          "Text": "docx mock text",
          "Confidence": 100.0,
        },
      ]
    },
  )
  file_path = GZIP_FIXTURES_DIR / "docxfile.docx.gz"
  payload = _run(_upload(api_module, file_path.name, file_path.read_bytes()))
  _assert_success_payload(payload)
  _assert_saved_json(tmp_path, "docxfile")
def test_upload_gz_pptx_success_and_writes_output(
  api_module: ModuleType,
  monkeypatch: pytest.MonkeyPatch,
  tmp_path: Path,
) -> None:
  monkeypatch.setattr(
    api_module,
    "_create_textract_blocks_from_pptx",
    lambda _: {
      "Blocks": [
        {"BlockType": "PAGE", "Page": 1, "Id": "page-pptx"},
        {
          "BlockType": "LINE",
          "Page": 1,
          "Id": "line-pptx",
          "Text": "pptx mock text",
          "Confidence": 100.0,
        },
      ]
    },
  )
  file_path = GZIP_FIXTURES_DIR / "pptxfile.pptx.gz"
  payload = _run(_upload(api_module, file_path.name, file_path.read_bytes()))
  _assert_success_payload(payload)
  _assert_saved_json(tmp_path, "pptxfile")
@pytest.mark.parametrize(
  "fixture_name, expected_inner_filename, expected_output_stem",
  [
    ("pdffile.pdf.gz", "pdffile.pdf", "pdffile"),
    ("jpegimage.jpeg.gz", "jpegimage.jpeg", "jpegimage"),
    ("pngimage.png.gz", "pngimage.png", "pngimage"),
  ],
)

def test_upload_gz_binary_types_use_textract_and_write_output(
  api_module: ModuleType,
  monkeypatch: pytest.MonkeyPatch,
  tmp_path: Path,
  fixture_name: str,
  expected_inner_filename: str,
  expected_output_stem: str,
) -> None:
  calls: list[tuple[bytes, str]] = []

  async def fake_extract_text_with_filename(document_bytes: bytes, filename: str) -> dict[str, Any]:
    calls.append((document_bytes, filename))
    return {
      "Blocks": [
        {"BlockType": "PAGE", "Page": 1, "Id": "page-1"},
        {
          "BlockType": "LINE",
          "Page": 1,
          "Id": "line-1",
          "Text": f"mock text for {filename}",
          "Confidence": 100.0,
        },
      ]
    }
  monkeypatch.setattr(api_module.textract_client, "extract_text_with_filename", fake_extract_text_with_filename)
  file_path = GZIP_FIXTURES_DIR / fixture_name
  payload = _run(_upload(api_module, file_path.name, file_path.read_bytes()))
  _assert_success_payload(payload)
  _assert_saved_json(tmp_path, expected_output_stem)
  assert len(calls) == 1
  assert calls[0][1] == expected_inner_filename
def test_upload_rejects_non_gzip_payload_and_writes_verbose_error_json(
  api_module: ModuleType,
  tmp_path: Path,
) -> None:
  bad_payload = (RAW_FIXTURES_DIR / "txtfile.txt").read_bytes()
  with pytest.raises(HTTPException) as exc_info:
    _run(_upload(api_module, "txtfile.txt.gz", bad_payload))
  exc = exc_info.value
  assert exc.status_code == 400
  assert isinstance(exc.detail, dict)
  detail = cast(dict[str, Any], exc.detail)
  assert detail["message"] == "Invalid upload encoding."
  assert "not a valid gzip stream" in detail["reason"]
  error_path = tmp_path / "tmp" / "error.json"
  assert error_path.exists()
  error_payload = json.loads(error_path.read_text(encoding="utf-8"))
  assert error_payload["error"]["status_code"] == 400
  assert error_payload["error"]["detail"]["message"] == "Invalid upload encoding."
  assert "hint" not in error_payload["error"]["detail"]
def test_upload_rejects_unsupported_type_and_writes_verbose_error_json(
  api_module: ModuleType,
  tmp_path: Path,
) -> None:
  file_path = GZIP_FIXTURES_DIR / "bash.sh.gz"
  with pytest.raises(HTTPException) as exc_info:
    _run(_upload(api_module, file_path.name, file_path.read_bytes()))
  exc = exc_info.value
  assert exc.status_code == 400
  assert isinstance(exc.detail, dict)
  detail = cast(dict[str, Any], exc.detail)
  assert detail["message"] == "Unsupported file type."
  assert "received extension '.sh'".lower() in detail["reason"].lower()
  assert ".pdf" in detail["allowed_extensions"]
  assert "hint" not in detail
  error_path = tmp_path / "tmp" / "error.json"
  assert error_path.exists()
  error_payload = json.loads(error_path.read_text(encoding="utf-8"))
  assert error_payload["error"]["status_code"] == 400
  assert error_payload["error"]["detail"]["message"] == "Unsupported file type."
  assert "hint" not in error_payload["error"]["detail"]
def test_upload_missing_filename_reports_non_existent_or_unnamed(
  api_module: ModuleType,
  tmp_path: Path,
) -> None:
  with pytest.raises(HTTPException) as exc_info:
    _run(_upload(api_module, "", gzip.compress(b"hello")))
  exc = exc_info.value
  assert exc.status_code == 400
  assert isinstance(exc.detail, dict)
  detail = cast(dict[str, Any], exc.detail)
  assert detail["message"] == "File upload is missing a filename."
  assert "non-existent or unnamed" in detail["reason"]
  error_path = tmp_path / "tmp" / "error.json"
  assert error_path.exists()
  error_payload = json.loads(error_path.read_text(encoding="utf-8"))
  assert error_payload["error"]["status_code"] == 400
  assert "non-existent or unnamed" in error_payload["error"]["detail"]["reason"]
def test_error_json_overwrites_with_latest_error(api_module: ModuleType, tmp_path: Path) -> None:
  with pytest.raises(HTTPException):
    _run(_upload(api_module, "", gzip.compress(b"x")))
  with pytest.raises(HTTPException):
    _run(_upload(api_module, "bad.exe.gz", gzip.compress(b"hello")))
  error_path = tmp_path / "tmp" / "error.json"
  payload = json.loads(error_path.read_text(encoding="utf-8"))
  assert payload["error"]["detail"]["message"] == "Unsupported file type."
