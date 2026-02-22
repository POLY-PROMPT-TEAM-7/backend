# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-21
**Commit:** 209432e
**Branch:** duckdb-prototype

## OVERVIEW
FastAPI backend for the KG Study Tool. LangGraph pipeline extracts entities/relationships and builds knowledge graphs; Nix manages build/dev.

**Tech Stack**: Python 3.13+, FastAPI, Pydantic, LangGraph, uvicorn, Nix

## STRUCTURE
```
./
├── flake.nix                     # Nix flake, deploy-backend + docker build
├── pyproject.toml                # Project metadata, console scripts
├── AGENTS.md                     # This file
├── lib/backend_placeholder/      # Python package
│   ├── api.py                    # FastAPI APP + routes
│   ├── agent.py                  # LangGraph pipeline builder
│   ├── state.py                  # KnowledgeExtractionState
│   ├── models.py                 # Pydantic models
│   ├── server.py                 # runner() -> uvicorn.run(APP)
│   ├── database.py               # DuckDB schema notes (no logic)
│   ├── services/                 # API-facing service layer
│   │   ├── upload_service.py      # Gzip ingest + artifact creation
│   │   ├── extract_service.py     # Pipeline run + DB persistence
│   │   ├── query_service.py       # Relationship/subgraph query wrappers
│   │   ├── path_safety.py         # Upload sandbox + path validation
│   │   ├── textract_adapter.py    # Timeout-guarded textract bridge
│   │   └── errors.py              # ServiceError contract
│   ├── nodes/                    # LangGraph workflow nodes
│   │   ├── extract_graph.py       # LLM extraction + retry
│   │   ├── validate_graph.py      # Validation rules
│   │   ├── mkgraph.py             # KnowledgeGraph construction
│   │   ├── schema_options.py      # Schema injection
│   │   ├── retry_flow.py          # Retry routing
│   │   └── link_canvas.py         # Canvas assignment linking
│   └── integrations/             # External API adapters
│       ├── enrich_openalex.py     # OpenAlex enrichment
│       └── canvas.py              # Canvas LMS
├── nix/
│   ├── docker.nix                 # dockerTools.buildImage
│   ├── overlay.nix                # Python package overlay
│   └── shell.nix                  # Dev shell
└── .github/workflows/docs.yml     # Build + push GHCR docker image
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| FastAPI app + routes | lib/backend_placeholder/api.py | APP constant, /extract endpoint |
| Pipeline orchestration | lib/backend_placeholder/agent.py | StateGraph, PIPELINE, process_document() |
| State schema | lib/backend_placeholder/state.py | KnowledgeExtractionState TypedDict |
| Models | lib/backend_placeholder/models.py | ExtractRequest/Response, payloads |
| Service layer | lib/backend_placeholder/services/AGENTS.md | Upload/extract/query orchestration |
| Nodes overview | lib/backend_placeholder/nodes/AGENTS.md | Node conventions + flow |
| Integrations overview | lib/backend_placeholder/integrations/AGENTS.md | API conventions + endpoints |
| Docker image build | nix/docker.nix | buildImage config + CMD |
| Nix overlay | nix/overlay.nix | buildPythonApplication deps |
| CI pipeline | .github/workflows/docs.yml | Nix build + GHCR publish |

## CONVENTIONS (Project-Level)
- **LangGraph nodes** return partial state dicts; never mutate state in place
- **Pipeline errors** accumulate in `validation_errors[]`/`processing_log[]` and continue
- **Nix-first workflow**: dev shell + docker build via flake (no Dockerfile)
- **Linting**: `flake8` is used; `ruff` and `pylint` are disabled in `pyproject.toml`
- **Service boundary**: API handlers translate `ServiceError` into HTTP responses

## ANTI-PATTERNS (THIS PROJECT)
- **NEVER** return full KnowledgeExtractionState from nodes
- **NEVER** mutate state in place; always return new values
- **DO NOT** stop pipeline on validation errors; accumulate and proceed
- **NO** hard-coded API endpoints; use constants
- **NEVER** retry indefinitely in integrations (single attempt)
- **DO NOT** replace original extraction; merge into `enriched_*`
- **DO NOT** allow unsandboxed artifact paths; enforce upload root and `.json` suffix

## UNIQUE STYLES
- **Package layout**: `lib/backend_placeholder/` (not `src/`)
- **Pipeline constant**: compiled graph stored as `PIPELINE`
- **CI docker from flake**: `nix build .#docker` + GHCR publish
- **Upload limits**: 20 MiB compressed and 100 MiB decompressed caps in service layer

## COMMANDS
```bash
nix develop
deploy-backend
nix run .#deploy-backend
nix build .#docker
flake8 lib/
```

## NOTES
- Tests not configured (no pytest/tox config)
- Docker image name: `backend-placeholder:latest`, port 8000/tcp
- `doCheck=false` in overlay for package build
- study-ontology overlay provides schema models
