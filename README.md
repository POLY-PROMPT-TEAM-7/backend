# Backend API - Document Processing

FastAPI-based backend service for extracting and parsing documents using AWS Textract.

## Project Structure

```
backend/
├── lib/
│   ├── backend_placeholder/
│   │   └── api.py              # Main FastAPI app with /api/documents/extract endpoint
│   └── document_processor/
│       ├── __init__.py         # Module exports
│       ├── api.py              # extract_document function (async)
│       ├── models.py           # Pydantic models (Document, Page, Line, Word)
│       └── parser.py           # DocumentParser for processing Textract blocks
├── tests/
│   └── document_processor/
│       ├── test_api.py         # 11 tests for API endpoint
│       ├── test_parser.py      # 7 tests for DocumentParser
│       └── test_integration.py # Placeholder for integration tests
├── INSTRUCTIONS.md             # Project task list
├── AWS_SETUP.md                # AWS setup guide
└── pyproject.toml              # Dependencies
```

## Document Processing Flow

```
Upload File
    ↓
Validate (size < 10MB, allowed extension)
    ↓
Extract text with AWS Textract
    ↓
Parse Textract blocks
    ↓
Return structured JSON (pages, lines, metadata)
```

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -e .
pip install pytest pytest-asyncio
```

### 2. Configure AWS Credentials (Optional for tests)

Tests use mocks and don't require AWS credentials. For production or integration tests:

```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"
```

See [AWS_SETUP.md](AWS_SETUP.md) for detailed instructions.

### 3. Run Tests

```bash
# Run all tests
PYTHONPATH=. pytest tests/ -v

# Run specific test suites
PYTHONPATH=. pytest tests/document_processor/test_parser.py -v
PYTHONPATH=. pytest tests/document_processor/test_api.py -v

# Run with coverage
PYTHONPATH=. pytest tests/ --cov=lib --cov-report=html
```

### 4. Start the API Server

```bash
# Using uvicorn
uvicorn lib.backend_placeholder.api:APP --reload --host 0.0.0.0 --port 8000

# Using server.py
python lib/backend_placeholder/server.py
```

## API Endpoints

### POST `/api/documents/extract`

Extract structured text from a document file.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: `file` (UploadFile)

**Constraints:**
- Max file size: 10MB
- Allowed extensions: .pdf, .pptx, .docx, .txt

**Response (200 OK):**
```json
{
  "pages": [
    {
      "page_number": 1,
      "lines": [
        {
          "line_number": 1,
          "text": "Sample line text",
          "confidence": 99.5,
          "words": [
            {
              "word_number": 1,
              "text": "Sample",
              "confidence": 99.8
            }
          ]
        }
      ]
    }
  ],
  "processing_time_ms": 1234,
  "document_id": "uuid-string",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**
- 400 Bad Request: Invalid file size or extension
- 500 Internal Server Error: Unexpected error
- 503 Service Unavailable: AWS Textract API error

## Example Usage

### Using curl

```bash
curl -X POST "http://localhost:8000/api/documents/extract" \
  -F "file=@document.pdf"
```

### Using Python requests

```python
import requests

url = "http://localhost:8000/api/documents/extract"
files = {"file": open("document.pdf", "rb")}
response = requests.post(url, files=files)

if response.status_code == 200:
    result = response.json()
    print(f"Document ID: {result['document_id']}")
    print(f"Pages: {len(result['pages'])}")
    print(f"Processing time: {result['processing_time_ms']}ms")
```

### Using JavaScript fetch

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/api/documents/extract', {
  method: 'POST',
  body: formData
})
  .then(response => response.json())
  .then(result => console.log(result));
```

## Library Usage

### Extract and Parse a Document

```python
from lib.document_processor import DocumentParser, TextractClient
import uuid

# Initialize Textract client
client = TextractClient()

# Extract text from document
with open("document.pdf", "rb") as f:
    file_bytes = f.read()
response = await client.extract_text(file_bytes)

# Parse of response
blocks = response.get("Blocks", [])
parser = DocumentParser(blocks)
document = parser.parse()

print(f"Document ID: {document.document_id}")
print(f"Pages: {len(document.pages)}")
print(f"Total lines: {sum(len(page.lines) for page in document.pages)}")
```

### Use the API Function Directly

```python
from lib.document_processor.api import extract_document
from fastapi import UploadFile

# Create an UploadFile object from bytes
from io import BytesIO
file = UploadFile(
    filename="document.pdf",
    file=BytesIO(file_bytes),
    content_type="application/pdf"
)

# Extract document
result = await extract_document(file)
print(result)
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AWS_ACCESS_KEY_ID` | AWS access key | - | No* |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - | No* |
| `AWS_REGION` | AWS region | `us-east-1` | No |

*Required for production, optional for tests (tests use mocks)

### Textract Configuration

Edit `lib/document_processor/client.py` to customize:
- AWS region
- Feature types (TABLES, FORMS, LAYOUT)
- Async/Await mode

## Development

### Running Tests with Coverage

```bash
PYTHONPATH=. pytest tests/ --cov=lib --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Linting

```bash
# Using ruff (recommended)
ruff check lib/ tests/
ruff format lib/ tests/

# Or using pylint (if configured)
pylint lib/ tests/
```

### Adding New Features

1. Add models to `lib/document_processor/models.py`
2. Implement logic in `lib/document_processor/parser.py` or create new modules
3. Add tests in `tests/document_processor/`
4. Update this README with new usage examples

## Troubleshooting

### Common Issues

**Problem:** `NoCredentialsError: Unable to locate credentials`
- **Solution:** Configure AWS credentials (see [AWS_SETUP.md](AWS_SETUP.md))

**Problem:** Tests fail with import errors
- **Solution:** Run with `PYTHONPATH=.` set: `PYTHONPATH=. pytest tests/`

**Problem:** File too large error (10MB)
- **Solution:** Reduce file size or update `MAX_FILE_SIZE` constant in `lib/document_processor/api.py`

**Problem:** Unsupported file extension
- **Solution:** Convert to supported format (.pdf, .pptx, .docx, .txt) or update `ALLOWED_EXTENSIONS`

## AWS Cost Information

Amazon Textract pricing (as of 2024):
- Documents < 1 page: $1.50 per 1,000 pages
- Documents 1+ pages: $15.00 per 1,000 pages
- Tables: $5.00 per 1,000 pages
- Forms: $5.00 per 1,000 pages

Free tier: 1,000 pages/month for first 3 months.

See [AWS Textract Pricing](https://aws.amazon.com/textract/pricing/) for details.

## Production Deployment

### Security Best Practices

1. Use AWS IAM roles instead of access keys when deploying to AWS
2. Enable AWS KMS encryption for documents
3. Set up VPC endpoints to keep traffic within your network
4. Implement rate limiting on the API endpoint
5. Add authentication/authorization middleware

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY backend/ .

RUN pip install -e .
RUN pip install uvicorn

EXPOSE 8000

CMD ["uvicorn", "lib.backend_placeholder.api:APP", "--host", "0.0.0.0", "--port", "8000"]
```

### CloudFormation/Terraform

Set up:
- Lambda function for API (if using serverless)
- EC2 instance or ECS container
- CloudFront CDN for static files
- S3 bucket for document storage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Add your license here]

## Support

For issues or questions:
- Check [AWS_SETUP.md](AWS_SETUP.md) for AWS-related issues
- Review test files for usage examples
- Open an issue on the repository
