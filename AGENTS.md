# Backend Development Guide

## Project Overview
FastAPI backend for KG Study Tool - a knowledge graph extraction and visualization system for course materials.

**Tech Stack**: Python 3.13+, FastAPI, Pydantic, uvicorn, Nix

---

## Development Commands

### Environment Setup
```bash
nix develop          # Enter development shell
```

### Running the Server
```bash
deploy-backend       # Runs uvicorn server on 0.0.0.0:8000
# or
nix run .#deploy-backend
```

### Linting
```bash
flake8 lib/          # Run linting on source code
```

### Building
```bash
nix build .#backend-placeholder    # Build the Python package
```

### Testing
Tests not yet configured. When adding tests, place them in `lib/backend_placeholder/tests/` and run:
```bash
pytest lib/backend_placeholder/tests/ -v                      # Run all tests
pytest lib/backend_placeholder/tests/test_module.py -v        # Run single test file
pytest lib/backend_placeholder/tests/test_module.py::test_func -v  # Run single test
```

---

## Code Style Guidelines

### Indentation & Formatting
- **2-space indentation** (strict)
- No trailing whitespace
- Max line length: ignored (E501 disabled)

### Type Hints
- Always use type hints in function signatures
- Use modern `dict[str, str]` syntax, not `Dict[str, str]`
- Return types required for all functions

```python
def serve(host: str = "0.0.0.0", port: int = 8000) -> None:
  uvicorn.run(APP, host=host, port=port)

@APP.get("/")
def placeholder() -> dict[str, str]:
  return {"placeholder": "placeholder"}
```

### Imports
- Group imports: standard library → third-party → local
- No blank lines between groups (E302 disabled)
- Prefer absolute imports over relative

```python
from backend_placeholder.api import APP  # Local imports first when referenced
from fastapi import FastAPI              # Third-party
import uvicorn                            # Standard library
```

### Pydantic Models
- All models inherit from `BaseModel`
- Place models in `models.py`
- Use simple, descriptive field names

```python
from pydantic import BaseModel

class Placeholder(BaseModel):
  Placeholder: str
```

### FastAPI Patterns
- Create app instance as module-level constant
- Use uppercase constant naming for app: `APP: FastAPI = FastAPI()`
- Define routes in `api.py`
- Use decorator pattern for route definitions

### File Structure
```
lib/backend_placeholder/
├── __init__.py      # Package marker (empty)
├── api.py           # FastAPI app and route definitions
├── models.py        # Pydantic models
└── server.py        # Server entry point with serve() function
```

### Naming Conventions
- **Modules**: lowercase_with_underscores
- **Classes**: PascalCase
- **Functions**: lowercase_with_underscores
- **Constants**: UPPER_CASE for module constants, PascalCase for app instances
- **Type hints**: Use descriptive names (e.g., `host: str` not `h: str`)

### Error Handling
- Not yet configured - follow FastAPI best practices
- Use HTTPException for HTTP errors
- Log errors appropriately
- Return meaningful error messages

### Linting Rules (Ignored)
The following flake8 errors are intentionally ignored:
- E501: Line length
- E111, E114, E117: Indentation
- E302, E305: Blank lines
- E121, E261, E203: Whitespace
- E731: Lambda functions
- W291, W293, W503: Trailing whitespace

---

## Dependencies
Core dependencies managed via Nix overlay:
- `study-ontology`: Knowledge graph schema models
- `pydantic`: Data validation
- `fastapi`: Web framework
- `uvicorn`: ASGI server

Dev tools:
- `flake8`: Linting
- `pyright`: Type checking (Microsoft)
- `pip`: Package management

---

## Project Context
This is the backend component of a hackathon project that extracts entities and relationships from course materials (PDFs, slides, notes) and builds an interactive knowledge graph. The backend handles document parsing, AI extraction, entity resolution, graph construction, and serves a REST API for the frontend.

**Key Features**:
- Document upload and parsing (PDF, PowerPoint, DOCX)
- AI-powered entity extraction with schema validation
- Graph construction with NetworkX
- Entity resolution and deduplication
- RESTful API for frontend integration

**Current Status**: Early development - basic FastAPI structure in place, extraction pipeline to be implemented.
