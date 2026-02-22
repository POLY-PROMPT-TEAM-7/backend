# Backend Package Knowledge Base

**Generated:** 2026-02-21
**Commit:** 209432e
**Branch:** duckdb-prototype

## OVERVIEW
FastAPI application orchestrating a LangGraph knowledge extraction pipeline with external API integrations.

## STRUCTURE
```
lib/backend_placeholder/
├── api.py                    # FastAPI app instance and routes
├── agent.py                  # LangGraph pipeline builder
├── state.py                  # Agent state management (TypedDict)
├── models.py                 # Pydantic models
├── server.py                 # Uvicorn runner
├── database.py               # DuckDB schema notes (no logic)
├── services/                 # API-facing orchestration layer
│   ├── upload_service.py      # Upload ingest + artifact JSON creation
│   ├── extract_service.py     # Pipeline invoke + DB persistence
│   ├── query_service.py       # Query API wrappers over DB helpers
│   ├── path_safety.py         # Upload root/path validation
│   ├── textract_adapter.py    # Timeout-protected textract bridge
│   └── errors.py              # ServiceError contract
├── nodes/                    # LangGraph workflow nodes
│   ├── extract_graph.py      # LLM entity extraction + retry
│   ├── validate_graph.py     # Entity/relationship validation
│   ├── mkgraph.py            # Graph construction
│   ├── schema_options.py     # Schema injection
│   ├── retry_flow.py         # Retry routing
│   └── link_canvas.py        # Canvas assignment linking
└── integrations/             # External API integrations
    ├── enrich_openalex.py    # OpenAlex concept enrichment
    └── canvas.py              # Canvas LMS integration
```
## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Pipeline orchestration | agent.py | PIPELINE constant, process_document() |
| FastAPI app instance | api.py | APP constant (uppercase) |
| API routes | api.py | @APP.get() decorator pattern |
| State definition | state.py | KnowledgeExtractionState TypedDict |
| Server entrypoint | server.py | runner(host, port) → uvicorn.run() |
| Pydantic models | models.py | BaseModel inheritance |
| Service layer | services/AGENTS.md | Upload/extract/query service contracts [View Map](services/AGENTS.md) |
| LangGraph nodes | nodes/AGENTS.md | Detailed node patterns [View Map](nodes/AGENTS.md) |
| External integrations | integrations/AGENTS.md | API patterns [View Map](integrations/AGENTS.md) |

## CONVENTIONS (Package-Level)
- **LangGraph nodes**: Functions receive `state: KnowledgeExtractionState`, return partial dict update
- **Pipeline flow**: inject_schema_options → (canvas_node + extract_graph) → validate_graph → retry_extract_graph → openalex_gate → enrich_with_openalex → link_canvas_assignments → mkgraph
- **Error handling**: Nodes append to validation_errors[]/processing_log[] and continue
- **State updates**: Always return dict with fields to update (not full state)
- **Service contract**: Services raise `ServiceError(status_code, error_code, message)` for API translation
- **Path safety**: Artifact paths must stay under `/tmp/backend-placeholder/uploads` and end with `.json`
- **API keys**: Loaded from env vars (OPENAI_API_KEY, OPENALEX_API_KEY, CANVAS_API_KEY)

## ANTI-PATTERNS (THIS PACKAGE)
- **NEVER** return full state from node functions - only update dicts
- **NEVER** mutate state in place - return new values
- **DO NOT** stop pipeline on validation errors - accumulate in validation_errors[]
- **NO** early returns from validate_graph - collect all errors
- **DO NOT** bypass `validate_artifact_path` before reading artifact JSON
- **DO NOT** remove upload size caps or extraction timeout guards

## UNIQUE STYLES
- **Package layout**: `lib/backend_placeholder/` (non-standard, typical is `src/` or `app/`)
- **Empty markers**: `__init__.py` files are empty (package markers only)
- **Pipeline constant**: Compiled graph stored in `PIPELINE` module-level constant
- **Conditional routing**: validate/openalex/enrichment nodes choose next hop
- **Service wrappers**: query services are thin typed adapters over `database.py` helpers

## COMMANDS
```bash
# Run server (via Nix)
nix run .#deploy-backend

# Lint
flake8 lib/backend_placeholder/
```

## NOTES
LangGraph StateGraph orchestrates extraction workflow
Integrations add enriched data to existing extraction results
Canvas API requires CalPoly-specific base URL
See [nodes/AGENTS.md](nodes/AGENTS.md) for LangGraph node conventions
See [integrations/AGENTS.md](integrations/AGENTS.md) for external API patterns
