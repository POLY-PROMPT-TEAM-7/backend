"""FastAPI document extraction endpoint"""
import time
from fastapi import UploadFile, HTTPException

from lib.document_processor.textract_client import TextractClient
from lib.document_processor.parser import DocumentParser

textract_client = TextractClient()


async def extract_document(file: UploadFile) -> dict:
    """Extract structured text from uploaded document.

    Args:
        file: Uploaded document file

    Returns:
        dict: Structured document with pages and metadata

    Raises:
        HTTPException: For validation errors, AWS errors, or processing failures
    """
    # Validate file size
    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB."
        )

    # Validate file extension
    allowed_extensions = {'.pdf', '.pptx', '.docx', '.txt'}
    file_ext = file.filename.rsplit('.', 1)[-1].lower() if file.filename else ''
    if f'.{file_ext}' not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Extract with Textract
    start_time = time.time()
    try:
        textract_response = await textract_client.extract_text(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(
            status_code=500,
            detail=f"AWS credentials error: {str(e)}. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

    # Parse into structured format
    blocks = textract_response.get('Blocks', [])
    parser = DocumentParser(blocks)
    document = parser.parse()
    document.processing_time_ms = int((time.time() - start_time) * 1000)

    return document.model_dump()
