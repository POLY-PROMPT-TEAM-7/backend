from unittest.mock import Mock, patch
import asyncio

import pytest
from botocore.exceptions import ClientError

from lib.document_processor.textract_client import TextractClient


@pytest.fixture
def mock_textract_client():
    mock = Mock()
    with patch("lib.document_processor.textract_client.boto3.client", return_value=mock):
        client = TextractClient()
    return client, mock


def test_textract_client_initialization():
    mock = Mock()
    with patch("lib.document_processor.textract_client.boto3.client", return_value=mock):
        client = TextractClient()
    assert client.client is not None
    assert client.poll_interval_seconds == 2
    assert client.max_poll_attempts == 150


def test_start_document_detection_success(mock_textract_client):
    client, mock_client = mock_textract_client
    mock_client.start_document_text_detection.return_value = {"JobId": "test-job-123"}

    job_id = asyncio.run(client.start_document_detection(b"test"))

    assert job_id == "test-job-123"
    mock_client.start_document_text_detection.assert_called_once()


def test_start_document_detection_unsupported_format(mock_textract_client):
    client, mock_client = mock_textract_client
    mock_client.start_document_text_detection.side_effect = ClientError(
        {
            "Error": {
                "Code": "UnsupportedDocumentException",
                "Message": "Unsupported document",
            }
        },
        "StartDocumentTextDetection",
    )

    with pytest.raises(ValueError, match="Unsupported document format"):
        asyncio.run(client.start_document_detection(b"test"))


def test_poll_job_completion_success(mock_textract_client):
    client, mock_client = mock_textract_client
    mock_client.get_document_text_detection.return_value = {"JobStatus": "SUCCEEDED"}

    result = asyncio.run(client.poll_job_completion("test-job"))

    assert result is True


def test_poll_job_completion_failure(mock_textract_client):
    client, mock_client = mock_textract_client
    mock_client.get_document_text_detection.return_value = {
        "JobStatus": "FAILED",
        "StatusMessage": "Invalid PDF",
    }

    with pytest.raises(RuntimeError, match="Textract job failed.*Invalid PDF"):
        asyncio.run(client.poll_job_completion("test-job"))


def test_poll_job_completion_timeout(mock_textract_client):
    client, mock_client = mock_textract_client
    client.max_poll_attempts = 3
    mock_client.get_document_text_detection.return_value = {
        "JobStatus": "IN_PROGRESS"
    }

    with patch("asyncio.sleep", return_value=None):
        with pytest.raises(RuntimeError, match="timed out"):
            asyncio.run(client.poll_job_completion("test-job"))


def test_extract_text_full_flow(mock_textract_client):
    client, mock_client = mock_textract_client

    mock_client.start_document_text_detection.return_value = {"JobId": "test-job"}
    mock_client.get_document_text_detection.side_effect = [
        {"JobStatus": "SUCCEEDED"},
        {"JobStatus": "SUCCEEDED", "Blocks": []},
    ]

    result = asyncio.run(client.extract_text(b"test"))

    assert "Blocks" in result
    mock_client.start_document_text_detection.assert_called_once()
    assert mock_client.get_document_text_detection.call_count == 2
