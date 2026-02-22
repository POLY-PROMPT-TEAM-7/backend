import gzip
import sqlite3
import tempfile
import os
import base64

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from .models import UploadResponse, ExtractResponse, UploadRequest

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

@APP.post("/upload")
def upload_document(file: UploadRequest) -> UploadResponse:
  if not file.file_path.endswith(".gz"):
    raise HTTPException(status_code=400, detail="Only .gz files are allowed")
  
  contents = base64.b64decode(file.content)
  decompressed= gzip.decompress(contents)
  text = decompressed.decode("utf-8")

  with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w") as temp_file:
    temp_file.write(text)

  return UploadResponse(text_path=temp_file.name)


@APP.post("/extract")
def extract_endpoint(upload_response: UploadResponse) -> ExtractResponse:
  file_path = upload_response.text_path
  if not os.path.exists(file_path):
    raise HTTPException(status_code=404, detail="File not found")

  with open(file_path, "r") as f:
    text = f.read()

  source_name = os.path.basename(file_path)
  conn = sqlite3.connect("study_tool.db")
  cursor = conn.cursor()
  
  cursor.execute("""
  CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    text TEXT
  )
  """)
  cursor.execute("INSERT INTO sources (name, text) VALUES (?, ?)", (source_name, text))

  source_id = cursor.lastrowid
  conn.commit()
  conn.close() #closing connection

  return ExtractResponse(source_id=source_id, source_name=source_name)


