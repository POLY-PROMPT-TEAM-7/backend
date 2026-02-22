# LangGraph Workflow Nodes

**Generated:** 2026-02-21
**Commit:** 209432e
**Branch:** duckdb-prototype

## OVERVIEW
LangGraph workflow nodes for knowledge extraction, validation, enrichment routing, and graph construction.

## STRUCTURE
```
lib/backend_placeholder/nodes/
├── extract_graph.py      # LLM extraction + retry
├── validate_graph.py     # Entity/relationship validation
├── mkgraph.py            # KnowledgeGraph construction
├── schema_options.py     # Schema injection into LLM context
├── retry_flow.py         # Retry orchestration
├── link_canvas.py        # Canvas assignment linking
└── __init__.py           # Empty package marker
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Entity extraction | extract_graph.py | Structured output + retry prompts |
| Validation logic | validate_graph.py | Checks IDs, types, references |
| Graph building | mkgraph.py | KnowledgeGraph from StudyOntology |
| Schema context | schema_options.py | Builds entity/relationship options |
| Retry flow | retry_flow.py | Routes extraction retries |
| Canvas linking | link_canvas.py | Adds COVERS/ASSESSED_BY relationships |

## CONVENTIONS (Node-Level)
- **Function signature**: `def node_name(state: KnowledgeExtractionState) -> dict[str, Any]`
- **Return value**: Partial state update (fields only, not full state)
- **Error handling**: Append to `validation_errors[]`, don't raise exceptions
- **Logging**: Append to `processing_log[]` with timestamps/status
- **State keys**: `raw_entities`, `raw_relationships`, `enriched_*`, `knowledge_graph`, `validation_errors`, `processing_log`

## ANTI-PATTERNS (NODES)
- **NEVER** return full KnowledgeExtractionState - only updated fields
- **NEVER** mutate state in place - return new dict
- **DO NOT** stop pipeline on errors - accumulate and continue
- **NO** side effects outside state (no external calls except integrations/)

## UNIQUE STYLES
- **LLM extraction**: Uses `ChatOpenAI.with_structured_output(ExtractedGraphPayload)`
- **Retry prompts**: Separate `build_retry_prompt()` with validation errors context
- **Validation**: Accumulates all errors (no early exit) for comprehensive feedback
- **Graph construction**: Filters entities by type before building graph

## FLOW
1. **schema_options** → Injects entity/relationship schema into state
2. **extract_graph** → LLM extracts raw_entities, raw_relationships
3. **validate_graph** → Validates IDs, types, references
4. **retry_flow** → Routes to retry_extract_graph or done based on errors
5. **link_canvas** → Links Canvas assignments to concepts
6. **mkgraph** → Builds KnowledgeGraph from validated data
7. **END**

## NOTES
- Each node is pure function (no class instances)
- Pipeline orchestration in parent `agent.py`
- Validation errors block graph construction but not pipeline flow
