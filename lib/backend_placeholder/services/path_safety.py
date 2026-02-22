from backend_placeholder.services.errors import ServiceError
from pathlib import Path
from uuid import uuid4
import re

UPLOAD_ROOT: Path = Path("/tmp/backend-placeholder/uploads")

def ensure_upload_root() -> Path:
  UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
  return UPLOAD_ROOT

def normalize_filename(filename: str) -> str:
  trimmed = Path(filename).name
  cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", trimmed)
  if not cleaned:
    return "upload"
  return cleaned

def build_upload_path(suffix: str) -> Path:
  root = ensure_upload_root().resolve(strict=False)
  return (root / f"{uuid4().hex}{suffix}").resolve(strict=False)

def build_artifact_path(source_id: str) -> Path:
  root = ensure_upload_root().resolve(strict=False)
  return (root / f"artifact-{source_id}.json").resolve(strict=False)

def validate_artifact_path(path_value: str | Path) -> Path:
  candidate = Path(path_value).expanduser()
  resolved = candidate.resolve(strict=False)
  root = ensure_upload_root().resolve(strict=False)
  try:
    resolved.relative_to(root)
  except ValueError as exc:
    raise ServiceError(400, "artifact_path_not_allowed", "artifact_path must be under upload root") from exc
  if resolved.suffix.lower() != ".json":
    raise ServiceError(400, "artifact_path_invalid_suffix", "artifact_path must point to a .json artifact")
  return resolved
