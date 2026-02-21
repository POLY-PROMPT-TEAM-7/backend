"""
Integration test for document processing API with real AWS Textract.

This test requires:
- Valid AWS credentials configured (see AWS_SETUP.md)
- A real document file to upload

Run with:
  pytest tests/document_processor/test_integration.py -v
  # Or skip tests if no credentials:
  pytest tests/document_processor/test_integration.py -v -m "not integration"
"""
import pytest
import os
from pathlib import Path


def test_integration_placeholder():
    """Placeholder for future integration tests.

    When you're ready to test with real AWS:

    1. Configure AWS credentials (see AWS_SETUP.md)
    2. Add a test document (tests/fixtures/test_document.pdf)
    3. Implement real integration test below

    Example:

    def test_extract_document_real():
        from lib.backend_placeholder.api import APP
        client = TestClient(APP)

        test_file = Path(__file__).parent / "fixtures" / "test_document.pdf"
        with open(test_file, "rb") as f:
            response = client.post(
                "/api/documents/extract",
                files={"file": ("test.pdf", f, "application/pdf")}
            )

        assert response.status_code == 200
        result = response.json()
        assert "pages" in result
        assert "document_id" in result
        assert "processing_time_ms" in result
    """
    pytest.skip(
        "Integration test not yet implemented. "
        "Requires AWS credentials and test documents. "
        "See AWS_SETUP.md for setup instructions."
    )


@pytest.mark.skipif(
    not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"),
    reason="AWS credentials not configured"
)
def test_integration_with_real_aws():
    """Test with real AWS Textract (when credentials are available)."""
    pytest.skip("Implement this when ready for real integration testing")
