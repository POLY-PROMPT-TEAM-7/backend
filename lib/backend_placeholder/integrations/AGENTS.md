# External API Integrations

**Generated:** 2026-02-21
**Commit:** 209432e
**Branch:** duckdb-prototype

## OVERVIEW
External API integrations for enriching extracted knowledge graphs with academic and LMS data.

## STRUCTURE
```
lib/backend_placeholder/integrations/
├── enrich_openalex.py    # OpenAlex concept enrichment
├── canvas.py              # Canvas LMS integration
└── __init__.py            # Empty package marker
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Concept enrichment | enrich_openalex.py | OpenAlex API (prerequisite, related, papers) |
| Canvas courses | canvas.py | CalPoly Canvas LMS API |
| API keys | Environment vars | OPENALEX_API_KEY, CANVAS_API_KEY |

## CONVENTIONS (Integration-Level)
- **HTTP client**: Use `httpx` with 30s timeout
- **Error handling**: Return empty lists/dicts on failures, log errors
- **Deduplication**: Merge by entity ID to avoid duplicates
- **State updates**: Add to `enriched_entities`, `enriched_relationships`, keep originals
- **Logging**: Append to `processing_log[]` with API call details

## ANTI-PATTERNS (INTEGRATIONS)
- **NEVER** block pipeline on API failures - return empty data, log error
- **DO NOT** replace original extraction - merge with `enriched_*` fields
- **NO** hard-coded API endpoints - use constants
- **NEVER** retry indefinitely - single attempt per node

## UNIQUE STYLES
- **OpenAlex enrichment**: Adds PREREQUISITE_OF, CONTRASTS_WITH, APPLIES_TO relationships
- **Canvas integration**: Filters courses by workflow_state=\"available\"
- **Provenance tracking**: `make_provenance()` records API source
- **Deduplication**: Merge by entity ID, keep original + enriched

## API DETAILS

### OpenAlex
- **Base URL**: `https://api.openalex.org`
- **Timeout**: 30s
- **Endpoints**:
  - `/concepts?search={name}` - Search concepts
  - `/concepts/{id}/works` - Get top papers
- **Enrichment types**:
  - Ancestor concepts → PREREQUISITE_OF
  - Related concepts → CONTRASTS_WITH
  - Top papers → APPLIES_TO

### Canvas LMS
- **Base URL**: `https://canvas.calpoly.edu/api/v1/`
- **Auth**: Bearer token (CANVAS_API_KEY)
- **Endpoints**:
  - `/courses` - Get user courses
  - `/courses/{id}/assignments` - Get assignments
- **Filtering**: workflow_state=\"available\" only

## STATE FLOW
1. Integration receives state with `raw_entities`, `raw_relationships`
2. Calls external APIs for enrichment data
3. Merges results into `enriched_entities`, `enriched_relationships`
4. Appends errors/details to `processing_log`
5. Returns merged state (preserves original + adds enriched)

## NOTES
- Integrations are optional nodes (can be bypassed in pipeline)
- All external calls use environment-based API keys
- Timeouts prevent pipeline stalls
