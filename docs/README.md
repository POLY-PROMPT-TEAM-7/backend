# Backend API - Document Processing

FastAPI service for document ingestion and text parsing.

## Current Behavior

- Upload endpoint: `POST /api/documents/upload`
- Health endpoint: `GET /`
- All uploaded payloads are expected to be **gzip-compressed**.
- The API decompresses upload bytes first, then routes parsing by inner filename extension.

## Supported File Types

Supported inner extensions (after gzip decompression):

- `.txt`
- `.docx`
- `.pptx`
- `.pdf`
- `.jpeg`
- `.png`

Processing strategy:

- `.txt`: direct UTF-8 decode + block construction
- `.docx`: parsed with `python-docx`
- `.pptx`: parsed with `python-pptx`
- `.pdf/.jpeg/.png`: extracted through AWS Textract

## Response and Output Files

On success:

- API returns structured document JSON
- Also writes a copy to `tmp/<input-stem>.json`
  - Example: `report.pdf.gz` -> `tmp/report.json`

On error:

- API returns an HTTP error payload
- Also writes latest error to `tmp/error.json` (overwrites previous error)

## API Contract

### `POST /api/documents/upload`

Multipart form field:

- `file` (gzip payload)

Validation rules:

- Max compressed upload size: 10 MB
- Filename is required
- Inner extension must be one of supported types
- Payload must be valid gzip

## Project Layout

```text
backend/
├── lib/
│   ├── backend_placeholder/
│   │   ├── api.py
│   │   └── server.py
│   └── document_processor/
│       ├── models.py
│       ├── parser.py
│       └── textract_client.py
├── tests/
│   └── document_processor/
│       ├── test_upload_api.py
│       ├── run_curl_upload_tests.sh
│       ├── test_files/
│       └── test_files_gzip/
├── nix/
│   ├── overlay.nix
│   └── shell.nix
└── pyproject.toml
```

## Setup

### Nix (recommended)

```bash
nix shell
```

### Pip (alternative)

```bash
pip install -e .
pip install pytest pytest-asyncio
```

## Run the Server

From `backend/`:

```bash
deploy-backend
```

or

```bash
uvicorn backend_placeholder.server:APP --host 0.0.0.0 --port 8000
```

## Test Commands

### Automated pytest coverage for upload flow

```bash
nix shell --command pytest tests/document_processor/test_upload_api.py -q
```

### Curl-based fixture sweep

```bash
tests/document_processor/run_curl_upload_tests.sh
```

The script runs uploads for all files in `tests/document_processor/test_files_gzip/` and one intentional non-existent file path case.

## Example Curl

```bash
curl -X POST "http://127.0.0.1:8000/api/documents/upload" -F "file=@tests/document_processor/test_files_gzip/pdffile.pdf.gz"
```

## AWS Notes

- AWS credentials are required for `.pdf`, `.jpeg`, and `.png` uploads because those paths use Textract.
- `.txt`, `.docx`, and `.pptx` paths are parsed locally.
