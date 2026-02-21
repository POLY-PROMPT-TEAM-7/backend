from backend_placeholder.state import KnowledgeExtractionState
from StudyOntology.lib import KnowledgeRelationship
from StudyOntology.lib import RelationshipType
from StudyOntology.lib import KnowledgeEntity
from pydantic import ValidationError
from typing import Optional
from typing import Any

def validate_graph(state: KnowledgeExtractionState) -> dict[str, Any]:
  """
  Validate all entities and relationships in state.

  Checks:
  - Each entity passes its own Pydantic model validation
  - No duplicate entity IDs
  - Every relationship's subject/object references an existing entity ID
  - RelationshipType is a valid enum value
  - Confidence scores are in [0.0, 1.0]

  Returns validation_errors list (empty = success) so the conditional
  edge can route to retry or continue.
  """
  entities: list[KnowledgeEntity] = state.get("entities", [])
  relationships: list[KnowledgeRelationship] = state.get("raw_relationships", [])

  errors: list[str] = []

  entity_ids: set[str] = set()
  for x in entities:
    try:
      x.model_validate_json(x.as_json())
    except ValidationError as e:
      errors += [f'Entity "{getattr(x, "id", "?")}" failed validation: {e}']

    eid: Optional[str] = getattr(x, "id", None)
    if not eid:
      errors += [f'Entity "{getattr(x, "id", "?")}" has no ID']
    elif eid in entity_ids:
      errors += [f'Duplicate entity ID "{eid}"']
    else:
      entity_ids |= set(eid)

  valid_types: set[str] = set(x.value for x in RelationshipType)
  for x in relationships:
    if x.subject not in entity_ids:
      errors += [f'Relationship subject "{x.subject}" does not reference an existing entity ID']
    elif x.object not in entity_ids:  
      errors += [f'Relationship object "{x.object}" does not reference an existing entity ID']
    elif x.type not in valid_types:
      errors += [f'Relationship type "{x.type}" is not a valid enum value']
    elif x.confidence < 0.0 or x.confidence > 1.0:
      errors += [f'Relationship confidence "{x.confidence}" is not in [0.0, 1.0] for relationship "{x.subject}" -> "{x.type}" -> "{x.object}"']

  msg: str = f"[validate_graph] Checked {len(entities)} entities, {len(relationships)} relationships. Found {len(errors)} errors."
  return {"validation_errors": errors, "processing_log": state.get("processing_log", []) + [msg]}