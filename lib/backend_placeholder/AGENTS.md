# Backend Package Knowledge Base

**Generated:** 2026-02-21
**Commit:** b27da408

## OVERVIEW
FastAPI application orchestrating LangGraph knowledge extraction pipeline with external API integrations.

## STRUCTURE
```
lib/backend_placeholder/
├── api.py                    # FastAPI app instance and routes
├── agent.py                  # LangGraph pipeline builder
├── state.py                  # Agent state management (TypedDict)
├── models.py                 # Pydantic models
├── server.py                 # Uvicorn runner
├── nodes/                    # LangGraph workflow nodes
│   ├── extract_graph.py      # GPT-4o entity extraction
│   ├── validate_graph.py     # Entity/relationship validation
│   ├── mkgraph.py            # Graph construction
│   ├── schema_options.py     # Schema injection
│   └── retry_flow.py         # Retry logic
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
| LangGraph nodes | nodes/AGENTS.md | Detailed node patterns [View Map](nodes/AGENTS.md) |
| External integrations | integrations/AGENTS.md | API patterns [View Map](integrations/AGENTS.md) |

## CONVENTIONS (Package-Level)
- **LangGraph nodes**: Functions receive `state: KnowledgeExtractionState`, return partial dict update
- **Pipeline flow**: inject_schema_options → extract_graph → validate_graph → (retry?) → mkgraph → END
- **Error handling**: Nodes return validation_errors[], processing_log[], continue pipeline
- **State updates**: Always return dict with fields to update (not full state)
- **API keys**: Loaded from env vars (OPENAI_API_KEY, OPENALEX_API_KEY, CANVAS_API_KEY)

## ANTI-PATTERNS (THIS PACKAGE)
- **NEVER** return full state from node functions - only update dicts
- **NEVER** mutate state in place - return new values
- **DO NOT** stop pipeline on validation errors - accumulate in validation_errors[]
- **NO** early returns from validate_graph - collect all errors

## UNIQUE STYLES
- **Package layout**: `lib/backend_placeholder/` (non-standard, typical is `src/` or `app/`)
- **Empty markers**: `__init__.py` files are empty (package markers only)
- **Pipeline constant**: Compiled graph stored in `PIPELINE` module-level constant
- **Route conditional**: `route_after_validate()` determines retry flow

## COMMANDS
```bash
# Run server (via Nix)
nix run .#deploy-backend

# Lint
flake8 lib/backend_placeholder/
```

## NOTES
LangGraph StateGraph orchestrates extraction workflow
State flows through nodes sequentially, accumulating entities/relationships
Integrations add enriched data to existing extraction results
Canvas API requires CalPoly-specific base URL
See [nodes/AGENTS.md](nodes/AGENTS.md) for LangGraph node conventions
See [integrations/AGENTS.md](integrations/AGENTS.md) for external API patterns
