# from fastapi import FastAPI

# APP: FastAPI = FastAPI()

# @APP.get("/")
# def placeholder() -> dict[str, str]:
#   return {"placeholder": "placeholder"}


from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import io

from .agent import process_document

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
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF, extract text, run the LangGraph pipeline,
    return the knowledge graph.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files supported right now")

    # Extract text from PDF
    contents = await file.read()
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        extracted_text = "\n".join(
            page.extract_text() or "" for page in pdf.pages
        )

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")

    # Run the full LangGraph pipeline
    result = process_document(
        filename=file.filename,
        extracted_text=extracted_text
    )

    # Return graph data to frontend
    return {
        "filename": result["filename"],
        "graph_stats": result["graph_stats"],
        "processing_log": result["processing_log"],
        "knowledge_graph": {
            "entities": [e.dict() for e in result["raw_entities"]],
            "relationships": [r.dict() for r in result["raw_relationships"]]
        }
    }