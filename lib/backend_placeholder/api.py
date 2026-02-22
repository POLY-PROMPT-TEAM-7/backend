import time
import uuid
import json
import gzip
import importlib
from types import ModuleType
from typing import Any, Mapping
from fastapi import UploadFile, HTTPException, FastAPI
from pathlib import Path
from document_processor.textract_client import TextractClient
from document_processor.parser import DocumentParser
import io
from backend_placeholder.models import ExtractResponse
from backend_placeholder.models import ExtractRequest
from backend_placeholder.models import SourceRecord
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi import FastAPI
from pathlib import Path

APP = FastAPI(title="Document Processing API")

# Allow React frontend to talk to this API
APP.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["*"],
  allow_headers=["*"]
)

@APP.get("/")
def placeholder() -> dict[str, str]:
  return {"status": "ok", "service": "document-processor"}
@APP.post("/api/documents/upload")
async def upload_document(file: UploadFile) -> dict[str, Any]:
  try:
    return await extract_document(file)
  except HTTPException as exc:
    _write_error_json(file.filename, exc.detail, exc.status_code)
    raise
  except Exception as exc:
    _write_error_json(file.filename, str(exc), 500)
    raise HTTPException(status_code=500, detail=f"Processing error: {str(exc)}") from exc

textract_client = TextractClient()

def _write_error_json(filename: str | None, detail: object, status_code: int) -> None:
  tmp_dir = Path.cwd() / "tmp"
  tmp_dir.mkdir(parents=True, exist_ok=True)
  sanitized_detail = detail
  if isinstance(detail, Mapping):
    sanitized_detail = {k: v for k, v in detail.items() if k != "hint"}
  payload = {
    "error": {
      "filename": filename,
      "status_code": status_code,
      "detail": sanitized_detail,
    }
  }
  error_path = tmp_dir / "error.json"
  error_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

def _decompress_gzip_payload(file_bytes: bytes, filename: str) -> tuple[bytes, str]:
  try:
    decompressed = gzip.decompress(file_bytes)
  except OSError as exc:
    raise HTTPException(
      status_code=400,
      detail={
        "message": "Invalid upload encoding.",
        "reason": (
          "All uploads must be gzip-compressed before being sent to this endpoint, "
          "but the payload is not a valid gzip stream."
        ),
        "filename": filename,
      },
    ) from exc
  effective_filename = filename[:-3] if filename.lower().endswith(".gz") else filename
  return decompressed, effective_filename

def _create_textract_blocks_from_text(text: str) -> dict[str, list[dict[str, Any]]]:
  blocks = [{'BlockType': 'PAGE', 'Page':1, 'Id': f'page-{str(uuid.uuid4())}'}]
  lines = text.split('\n')
  for line_num, line in enumerate(lines, start=1):
    if line.strip():
      blocks.append({
        'BlockType': 'LINE',
        'Page': 1,
        'Text': line,
        'Confidence': 100.0,
        'Id': f'line-{str(uuid.uuid4())}'
      })
  return {'Blocks': blocks}

def _create_textract_blocks_from_docx(file_bytes: bytes) -> dict[str, list[dict[str, Any]]]:
  try:
    docx_module: ModuleType = importlib.import_module("docx")
    Document = getattr(docx_module, "Document")
  except ImportError as exc:
    raise ImportError("python-docx is required to process .docx files") from exc
  doc = Document(io.BytesIO(file_bytes))
  blocks = [{'BlockType': 'PAGE', 'Page': 1, 'Id': f'page-{str(uuid.uuid4())}'}]
  for para in doc.paragraphs:
    if para.text.strip():
      blocks.append({
        'BlockType': 'LINE',
        'Page': 1,
        'Text': para.text,
        'Confidence': 100.0,
        'Id': f'line-{str(uuid.uuid4())}'
      })
  return {'Blocks': blocks}

def _create_textract_blocks_from_pptx(file_bytes: bytes) -> dict[str, list[dict[str, Any]]]:
  try:
    pptx_module: ModuleType = importlib.import_module("pptx")
    pptx_shapes_module: ModuleType = importlib.import_module("pptx.enum.shapes")
    Presentation = getattr(pptx_module, "Presentation")
    MSO_SHAPE_TYPE = getattr(pptx_shapes_module, "MSO_SHAPE_TYPE")
  except ImportError as exc:
    raise ImportError("python-pptx is required to process .pptx files") from exc
  presentation = Presentation(io.BytesIO(file_bytes))
  blocks = []

  def append_line(text: str, page_number: int) -> None:
    stripped = text.strip()
    if not stripped:
      return
    blocks.append({
      "BlockType": "LINE",
      "Page": page_number,
      "Text": stripped,
      "Confidence": 100.0,
      "Id": f"line-{str(uuid.uuid4())}"
    })

  def extract_shape_text(shape: Any, page_number: int) -> None:
    shape_type = getattr(shape, "shape_type", None)
    if shape_type == MSO_SHAPE_TYPE.GROUP:
      for nested in shape.shapes:
        extract_shape_text(nested, page_number)
      return
    if getattr(shape, "has_text_frame", False) and shape.has_text_frame:
      append_line(shape.text_frame.text, page_number)
    if getattr(shape, "has_table", False) and shape.has_table:
      for row in shape.table.rows:
        for cell in row.cells:
          append_line(cell.text, page_number)
  for slide_idx, slide in enumerate(presentation.slides, start=1):
    blocks.append({
      "BlockType": "PAGE",
      "Page": slide_idx,
      "Id": f"page-{str(uuid.uuid4())}"
    })
    for shape in slide.shapes:
      extract_shape_text(shape, slide_idx)
  return {"Blocks": blocks}

async def extract_document(file: UploadFile) -> dict[str, Any]:
  file_bytes = await file.read()
  if len(file_bytes) > 10 * 1024 * 1024:
    raise HTTPException(
      status_code=400,
      detail={
        "message": "Uploaded file is too large.",
        "reason": "Maximum supported size is 10MB.",
        "received_bytes": len(file_bytes),
        "max_bytes": 10 * 1024 * 1024,
      },
    )
  allowed_extensions = {'.pdf', '.pptx', '.docx', '.txt', '.jpeg', '.png'}
  if not file.filename:
    raise HTTPException(
      status_code=400,
      detail={
        "message": "File upload is missing a filename.",
        "reason": "The uploaded file appears non-existent or unnamed in the multipart request.",
      },
    )
  file_bytes, effective_filename = _decompress_gzip_payload(file_bytes, file.filename)
  file_ext = Path(effective_filename).suffix.lower()
  if file_ext not in allowed_extensions:
    raise HTTPException(
      status_code=400,
      detail={
        "message": "Unsupported file type.",
        "reason": (
          f"Received extension '{file_ext or '[none]'}' from filename '{effective_filename}'. "
          "This API accepts only specific document/image formats."
        ),
        "allowed_extensions": sorted(allowed_extensions),
      },
    )
  start_time = time.time()
  if file_ext == '.txt':
    try:
      text_content = file_bytes.decode('utf-8')
      textract_response = _create_textract_blocks_from_text(text_content)
    except UnicodeDecodeError as e:
      raise HTTPException(
        status_code=400,
        detail=f"Failed to decode .txt file as UTF-8: {str(e)}"
      ) from e
  elif file_ext == '.docx':
    try:
      textract_response = _create_textract_blocks_from_docx(file_bytes)
    except ImportError as e:
      raise HTTPException(
        status_code=400,
        detail=str(e)
      )
    except Exception as e:
      raise HTTPException(
        status_code=400,
        detail=f"Failed to parse .docx file: {str(e)}"
      ) from e
  elif file_ext == '.pptx':
    try:
      textract_response = _create_textract_blocks_from_pptx(file_bytes)
    except ImportError as e:
      raise HTTPException(
        status_code=400,
        detail=str(e)
      )
    except Exception as e:
      raise HTTPException(
        status_code=400,
        detail=f"Failed to parse .pptx file: {str(e)}"
      ) from e
  else:
    try:
      textract_response = await textract_client.extract_text_with_filename(
        file_bytes,
        effective_filename,
      )
    except ValueError as e:
      raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
      raise HTTPException(
        status_code=503,
        detail=(
          f"AWS permissions/credentials error: {str(e)}. "
          "Verify AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY, and IAM permissions "
          "for S3 and Textract on configured bucket."
        )
      )
    except RuntimeError as e:
      raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
      raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
  blocks = textract_response.get('Blocks', [])
  parser = DocumentParser(blocks)
  document = parser.parse()
  document.processing_time_ms = int((time.time() - start_time) * 1000)
  tmp_dir = Path.cwd() / 'tmp'
  tmp_dir.mkdir(parents=True, exist_ok=True)
  output_filename = Path(effective_filename).stem + '.json'
  output_path = tmp_dir / output_filename
  output_path.write_text(json.dumps(document.model_dump(mode='json'), indent=2), encoding='utf-8')
  return document.model_dump(mode='json')
  return {"placeholder": "placeholder"}

source_records: list[SourceRecord] = []

@APP.post("/extract")
def extract_endpoint(upload_request: ExtractRequest) -> ExtractResponse:
  if not upload_request.text.exists():
    raise HTTPException(status_code=404, detail="File not found")

  source_name: str = upload_request.text.name
  source_id: int = len(source_records) + 1
  source_records.append(SourceRecord(
    source_id=source_id,
    source_name=source_name,
    text=Path(upload_request.text)
  ))

  return ExtractResponse(source_id=source_id, source_name=source_name)
