from backend_placeholder.services.textract_adapter import extract_text
from backend_placeholder.services.path_safety import build_artifact_path
from backend_placeholder.services.path_safety import build_upload_path
from backend_placeholder.services.path_safety import normalize_filename
from backend_placeholder.models import UploadArtifact
from backend_placeholder.models import UploadResponse
from datetime import UTC
from datetime import datetime
from backend_placeholder.services.errors import ServiceError
from fastapi import UploadFile
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

MAX_COMPRESSED_BYTES: int = 20 * 1024 * 1024
MAX_DECOMPRESSED_BYTES: int = 100 * 1024 * 1024
READ_CHUNK_SIZE: int = 1024 * 1024
EXTRACTION_TIMEOUT_SECONDS: int = 45

async def ingest_upload(upload_file: UploadFile) -> UploadResponse:
  normalized_filename = normalize_filename(upload_file.filename or "upload")
  upload_suffix = "".join(Path(normalized_filename).suffixes)
  upload_path = build_upload_path(upload_suffix)

  compressed_bytes = 0
  decompressed_bytes = 0
  digest = sha256()
  try:
    with upload_path.open("wb") as target:
      while True:
        chunk = await upload_file.read(READ_CHUNK_SIZE)
        if not chunk:
          break
        compressed_bytes += len(chunk)
        decompressed_bytes += len(chunk)
        if compressed_bytes > MAX_COMPRESSED_BYTES:
          raise ServiceError(413, "compressed_size_exceeded", "compressed upload exceeds 20 MiB")
        if decompressed_bytes > MAX_DECOMPRESSED_BYTES:
          raise ServiceError(413, "decompressed_size_exceeded", "decompressed payload exceeds 100 MiB")
        digest.update(chunk)
        target.write(chunk)
  finally:
    await upload_file.close()

  fallback_text = upload_path.read_text(encoding="utf-8", errors="replace")
  textract_result = extract_text(upload_path, timeout_seconds=EXTRACTION_TIMEOUT_SECONDS)
  extracted_text = textract_result.text.strip() or fallback_text
  if not extracted_text.strip():
    raise ServiceError(422, "empty_extracted_text", "unable to extract non-empty text from upload")

  source_id = uuid4().hex
  source_name = Path(normalized_filename).stem
  artifact_sha256 = digest.hexdigest()
  artifact_path = build_artifact_path(source_id)
  artifact_payload = UploadArtifact(
    source_id=source_id,
    source_name=source_name,
    original_filename=normalized_filename,
    extracted_text=extracted_text,
    artifact_sha256=artifact_sha256,
    metadata_status=textract_result.metadata_status,
    metadata_error_code=textract_result.error_code,
    metadata_error_message=textract_result.error_message,
    compressed_bytes=compressed_bytes,
    decompressed_bytes=decompressed_bytes,
    created_at=datetime.now(tz=UTC).isoformat(),
  )
  artifact_path.write_text(artifact_payload.model_dump_json(indent=2), encoding="utf-8")

  try:
    upload_path.unlink(missing_ok=True)
  except Exception:
    pass

  return UploadResponse(
    source_id=source_id,
    source_name=source_name,
    artifact_path=str(artifact_path),
    artifact_sha256=artifact_sha256,
    metadata_status=textract_result.metadata_status,
    metadata_error_code=textract_result.error_code,
    metadata_error_message=textract_result.error_message,
    compressed_bytes=compressed_bytes,
    decompressed_bytes=decompressed_bytes,
  )
