from fastapi import FastAPI, UploadFile

APP: FastAPI = FastAPI()


@APP.get("/")
def placeholder() -> dict[str, str]:
    return {"placeholder": "placeholder"}


@APP.post("/api/documents/extract")
async def upload_document(file: UploadFile):
    """Extract structured text from uploaded document.

    Accepts: PDF, PPTX, DOCX, TXT files (max 10MB)
    Returns: JSON with pages, lines, and metadata
    """
    from lib.document_processor.api import extract_document
    return await extract_document(file)
