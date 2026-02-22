from backend_placeholder.models import ExtractResponse
from backend_placeholder.models import ExtractRequest
from backend_placeholder.models import SourceRecord
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi import FastAPI
from pathlib import Path

APP: FastAPI = FastAPI()

# Allow React frontend to talk to this API
APP.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["*"],
  allow_headers=["*"]
)

@APP.get("/")
def placeholder() -> dict[str, str]:
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
