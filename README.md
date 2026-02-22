# Backend API

Simple FastAPI backend for knowledge graph extraction and query.

## Quick Start

```bash
nix develop
nix run .#deploy-backend
```

Server runs on `http://localhost:8000`.

## Environment Variables

Set these before starting the server:

- `OPENAI_API_KEY` (required): used by extraction nodes to call OpenAI.
- `OPENALEX_API_KEY` (optional): used only when OpenAlex enrichment is enabled (`query_openalex=true`).
- `CANVAS_API_KEY` (optional): used only when Canvas integration is enabled (`query_canvas=true`).

Example:

```bash
export OPENAI_API_KEY="your-openai-key"
export OPENALEX_API_KEY="your-openalex-key"   # optional
export CANVAS_API_KEY="your-canvas-key"       # optional
```

## API Routes

### Health

- `GET /health/`
  - Returns service health status.

### Upload + Extract

- `POST /upload`
  - Upload a `.gz` file.
  - Returns an artifact path/hash for later extraction.

- `POST /extract`
  - Runs graph extraction from an upload artifact.
  - Request body: `ExtractRequest`.
  - Response body: `ExtractResponse`.

### Query Routes

- `GET /query/relationships`
  - Query relationships with pagination and confidence filters.

- `GET /query/subgraph/source/{source_id}`
  - Query a subgraph by one source ID.

- `POST /query/subgraph/sources`
  - Query a subgraph by multiple source IDs.

- `GET /query/subgraph/entity/{entity_id_or_name}`
  - Query a subgraph by entity ID or name.

- `GET /query/relationships/type/{relationship_type}`
  - Query a subgraph by relationship type.

- `POST /query/subgraph/entity-types`
  - Query a subgraph by a list of entity types.

## Notes

- OpenAlex and Canvas are optional integrations.
- If optional API keys are missing, those enrichments are skipped gracefully.
