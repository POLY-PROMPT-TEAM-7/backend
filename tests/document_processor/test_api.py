"""Test FastAPI document extraction endpoint"""
import pytest
from fastapi import UploadFile, HTTPException
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from io import BytesIO

from lib.document_processor.models import Document, Page, Line


@pytest.fixture
def mock_boto3_client():
    """Mock boto3 client to prevent AWS initialization"""
    mock = Mock()
    with patch("lib.document_processor.textract_client.boto3.client", return_value=mock):
        yield mock


@pytest.fixture
def mock_textract_response():
    """Mock Textract response with BLOCKS"""
    return {
        "Blocks": [
            {"BlockType": "PAGE", "Id": "page1", "Page": 1},
            {"BlockType": "LINE", "Id": "line1", "Page": 1, "Text": "First line", "Confidence": 99.5},
            {"BlockType": "LINE", "Id": "line2", "Page": 1, "Text": "Second line", "Confidence": 98.0},
            {"BlockType": "PAGE", "Id": "page2", "Page": 2},
            {"BlockType": "LINE", "Id": "line3", "Page": 2, "Text": "Page 2 content", "Confidence": 97.5},
        ]
    }


@pytest.fixture
def extract_document(mock_boto3_client, mock_textract_response):
    """Get extract_document function with mocked clients"""
    from lib.document_processor.api import extract_document
    from unittest.mock import patch

    with patch('lib.document_processor.api.textract_client') as mock_tex:
        mock_tex.extract_text = AsyncMock(return_value=mock_textract_response)

        with patch('lib.document_processor.api.DocumentParser') as mock_parser_class:
            # Mock the parser instance and its parse method
            mock_parser_instance = mock_parser_class.return_value
            mock_doc = Document(
                pages=[
                    Page(page_number=1, text="First line\nSecond line", lines=[
                        Line(line_number=1, text="First line", confidence=0.995),
                        Line(line_number=2, text="Second line", confidence=0.98)
                    ]),
                    Page(page_number=2, text="Page 2 content", lines=[
                        Line(line_number=1, text="Page 2 content", confidence=0.975)
                    ])
                ],
                processing_time_ms=100
            )
            mock_parser_instance.parse.return_value = mock_doc
            yield extract_document


@pytest.mark.asyncio
async def test_extract_document_success(extract_document):
    """Test successful document extraction"""
    file = UploadFile(filename="test.pdf", file=BytesIO(b"test content"))

    result = await extract_document(file)

    assert "pages" in result
    assert len(result["pages"]) == 2
    assert "processing_time_ms" in result
    assert result["processing_time_ms"] >= 0
    assert "document_id" in result


@pytest.mark.asyncio
async def test_extract_document_file_too_large(mock_boto3_client):
    """Test rejection of oversized file"""
    from lib.document_processor.api import extract_document
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB
    file = UploadFile(filename="large.pdf", file=BytesIO(large_content))

    with pytest.raises(HTTPException) as exc_info:
        await extract_document(file)

    assert exc_info.value.status_code == 400
    assert "File too large" in exc_info.value.detail


@pytest.mark.asyncio
async def test_extract_document_unsupported_extension(mock_boto3_client):
    """Test rejection of unsupported file type"""
    from lib.document_processor.api import extract_document
    file = UploadFile(filename="test.exe", file=BytesIO(b"test content"))

    with pytest.raises(HTTPException) as exc_info:
        await extract_document(file)

    assert exc_info.value.status_code == 400
    assert "Unsupported file type" in exc_info.value.detail


@pytest.mark.asyncio
async def test_extract_document_supported_pdf(extract_document):
    """Test PDF file is accepted"""
    file = UploadFile(filename="document.pdf", file=BytesIO(b"pdf content"))

    result = await extract_document(file)

    assert result is not None


@pytest.mark.asyncio
async def test_extract_document_supported_pptx(extract_document):
    """Test PPTX file is accepted"""
    file = UploadFile(filename="presentation.pptx", file=BytesIO(b"pptx content"))

    result = await extract_document(file)

    assert result is not None


@pytest.mark.asyncio
async def test_extract_document_supported_docx(extract_document):
    """Test DOCX file is accepted"""
    file = UploadFile(filename="word.docx", file=BytesIO(b"docx content"))

    result = await extract_document(file)

    assert result is not None


@pytest.mark.asyncio
async def test_extract_document_supported_txt(extract_document):
    """Test TXT file is accepted"""
    file = UploadFile(filename="notes.txt", file=BytesIO(b"txt content"))

    result = await extract_document(file)

    assert result is not None


@pytest.mark.asyncio
async def test_extract_document_textract_value_error(mock_boto3_client):
    """Test handling of Textract ValueError"""
    from lib.document_processor.api import extract_document
    with patch('lib.document_processor.api.textract_client') as mock:
        mock.extract_text = AsyncMock(side_effect=ValueError("Invalid file format"))

        file = UploadFile(filename="bad.pdf", file=BytesIO(b"bad content"))

        with pytest.raises(HTTPException) as exc_info:
            await extract_document(file)

        assert exc_info.value.status_code == 400
        assert "Invalid file format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_extract_document_aws_permission_error(mock_boto3_client):
    """Test handling of AWS permission errors"""
    from lib.document_processor.api import extract_document
    with patch('lib.document_processor.api.textract_client') as mock:
        mock.extract_text = AsyncMock(
            side_effect=PermissionError("AWS credentials not found")
        )

        file = UploadFile(filename="test.pdf", file=BytesIO(b"test content"))

        with pytest.raises(HTTPException) as exc_info:
            await extract_document(file)

        assert exc_info.value.status_code == 500
        assert "AWS credentials error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_extract_document_runtime_error(mock_boto3_client):
    """Test handling of Textract service errors"""
    from lib.document_processor.api import extract_document
    with patch('lib.document_processor.api.textract_client') as mock:
        mock.extract_text = AsyncMock(
            side_effect=RuntimeError("Textract service unavailable")
        )

        file = UploadFile(filename="test.pdf", file=BytesIO(b"test content"))

        with pytest.raises(HTTPException) as exc_info:
            await extract_document(file)

        assert exc_info.value.status_code == 503
        assert "Textract service unavailable" in exc_info.value.detail


@pytest.mark.asyncio
async def test_extract_document_generic_exception(mock_boto3_client):
    """Test handling of unexpected errors"""
    from lib.document_processor.api import extract_document
    with patch('lib.document_processor.api.textract_client') as mock:
        mock.extract_text = AsyncMock(side_effect=Exception("Unexpected error"))

        file = UploadFile(filename="test.pdf", file=BytesIO(b"test content"))

        with pytest.raises(HTTPException) as exc_info:
            await extract_document(file)

        assert exc_info.value.status_code == 500
        assert "Processing error" in exc_info.value.detail
