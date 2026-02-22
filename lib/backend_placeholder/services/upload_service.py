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
import gzip
from uuid import uuid4

MAX_COMPRESSED_BYTES: int = 20 * 1024 * 1024
MAX_DECOMPRESSED_BYTES: int = 100 * 1024 * 1024
READ_CHUNK_SIZE: int = 1024 * 1024
EXTRACTION_TIMEOUT_SECONDS: int = 45

async def ingest_upload(upload_file: UploadFile) -> UploadResponse:
  normalized_filename = normalize_filename(upload_file.filename or "upload.gz")
  if not normalized_filename.lower().endswith(".gz"):
    raise ServiceError(400, "invalid_upload_type", "only .gz uploads are accepted")

  gz_path = build_upload_path(".gz")
  plain_path = build_upload_path(".txt")

  compressed_bytes = 0
  try:
    with gz_path.open("wb") as target:
      while True:
        chunk = await upload_file.read(READ_CHUNK_SIZE)
        if not chunk:
          break
        compressed_bytes += len(chunk)
        if compressed_bytes > MAX_COMPRESSED_BYTES:
          raise ServiceError(413, "compressed_size_exceeded", "compressed upload exceeds 20 MiB")
        target.write(chunk)
  finally:
    await upload_file.close()

  decompressed_bytes = 0
  digest = sha256()
  try:
    with gzip.open(gz_path, "rb") as source:
      with plain_path.open("wb") as target:
        while True:
          chunk = source.read(READ_CHUNK_SIZE)
          if not chunk:
            break
          decompressed_bytes += len(chunk)
          if decompressed_bytes > MAX_DECOMPRESSED_BYTES:
            raise ServiceError(413, "decompressed_size_exceeded", "decompressed payload exceeds 100 MiB")
          digest.update(chunk)
          target.write(chunk)
  except ServiceError:
    raise
  except Exception as exc:
    raise ServiceError(400, "invalid_gzip", f"unable to decompress gzip upload: {exc}") from exc

  fallback_text = plain_path.read_text(encoding="utf-8", errors="replace")
  textract_result = extract_text(plain_path, timeout_seconds=EXTRACTION_TIMEOUT_SECONDS)
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
    gz_path.unlink(missing_ok=True)
    plain_path.unlink(missing_ok=True)
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
