# Services Layer Knowledge Base

**Generated:** 2026-02-22
**Scope:** `lib/backend_placeholder/services/`

## OVERVIEW
Service-layer orchestration between FastAPI handlers, LangGraph pipeline execution, filesystem-safe upload handling, textract extraction, and DuckDB query/persistence helpers.

## STRUCTURE
```
lib/backend_placeholder/services/
├── upload_service.py          # Upload ingest, gzip safety, artifact JSON write
├── extract_service.py         # Artifact validation, pipeline run, DB persistence
├── query_service.py           # Typed query wrappers over DB functions
├── path_safety.py             # Upload root, filename normalization, path validation
├── textract_adapter.py        # Timeout-guarded textract adapter with error mapping
└── errors.py                  # ServiceError contract
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Handle `.gz` upload ingestion | `upload_service.py` | Enforces compressed/decompressed caps and writes `UploadArtifact` |
| Run extraction from artifact | `extract_service.py` | Validates artifact path/content, invokes `process_document()` |
| Translate domain failures to API | `errors.py` | `ServiceError(status_code, error_code, message)` |
| Enforce sandboxed artifact paths | `path_safety.py` | Upload root lock + `.json` suffix requirement |
| Run textract with timeout + classified errors | `textract_adapter.py` | Returns structured result, no uncaught adapter exceptions |
| Query relationships/subgraphs | `query_service.py` | Thin typed wrappers over `database.py` query helpers |

## CONVENTIONS
- Services raise `ServiceError` for expected client/domain failures; API layer maps these to HTTP responses.
- Upload and artifact paths must remain inside `/tmp/backend-placeholder/uploads`.
- Upload ingest is streaming and bounded (20 MiB compressed, 100 MiB decompressed).
- Text extraction favors textract but gracefully falls back to plaintext when parser tools are unavailable.
- Extraction workflow is idempotent on artifact hash via `get_processed_artifact(...)` checks.

## ANTI-PATTERNS
- **NEVER** trust user-provided artifact paths without `validate_artifact_path`.
- **DO NOT** remove size/time guards (`MAX_*` caps, textract timeout) in services.
- **DO NOT** raise raw library exceptions from service boundary when a `ServiceError` contract exists.
- **DO NOT** duplicate query logic in API handlers; keep DB access routed through `query_service.py`.

## UNIQUE STYLES
- `UploadArtifact` JSON is written with stable, explicit fields (`model_dump_json(indent=2)`) for traceability.
- `textract_adapter.extract_text(...)` returns structured status/error metadata instead of throwing outward.
- Query service methods are intentionally thin adapters to preserve response typing consistency.

## NOTES
- `EXTRACTION_TIMEOUT_SECONDS` defaults to 45s in upload flow.
- `path_safety.py` normalizes filenames with a conservative `[A-Za-z0-9._-]` whitelist.
- This layer is the primary policy boundary for upload safety and extraction reliability.
