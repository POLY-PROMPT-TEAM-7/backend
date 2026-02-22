from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from .models import ExtractResponse, SourceRecord, ExtractRequest
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
  if not Path(upload_request.text_path).exists():
    raise HTTPException(status_code=404, detail="File not found")

  source_name = Path(upload_request.text_path).name
  source_id = len(source_records) + 1
  source_records.append(SourceRecord(
    source_id=source_id,
    source_name=source_name,
    text_path=Path(upload_request.text_path)
  ))

  return ExtractResponse(source_id=source_id, source_name=source_name)


