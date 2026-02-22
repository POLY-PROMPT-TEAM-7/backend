from backend_placeholder.state import KnowledgeExtractionState
from StudyOntology.lib import KnowledgeRelationship
from StudyOntology.lib import RelationshipType
from StudyOntology.lib import KnowledgeEntity
from StudyOntology.lib import Assignment
from typing import Any

def validate_graph(state: KnowledgeExtractionState) -> dict[str, Any]:
  entities: list[KnowledgeEntity] = state.get("raw_entities", [])
  relationships: list[KnowledgeRelationship] = state.get("raw_relationships", [])

  errors: list[str] = []
  entity_ids: set[str] = set()

  for x in entities:
    eid: Any = getattr(x, "id", None)
    name: Any = getattr(x, "name", None)
    if not isinstance(eid, str) or not eid:
      errors += [f'Entity "{eid}" has no valid ID']
    elif isinstance(x, Assignment) and (not isinstance(name, str) or not name.strip()):
      errors += [f'Assignment entity "{eid}" has no valid name']
    elif eid in entity_ids:
      errors += [f'Duplicate entity ID "{eid}"']
    else:
      entity_ids.add(eid)

  valid_types: set[str] = set(x.value for x in RelationshipType)
  for x in relationships:
    subject: Any = getattr(x, "subject", None)
    obj: Any = getattr(x, "object", None)
    relation_type: Any = getattr(x, "predicate", None)
    confidence: Any = getattr(x, "confidence", None)

    if not isinstance(subject, str) or subject not in entity_ids:
      errors += [f'Relationship subject "{subject}" does not reference an existing entity ID']
    elif not isinstance(obj, str) or obj not in entity_ids:
      errors += [f'Relationship object "{obj}" does not reference an existing entity ID']
    elif not isinstance(relation_type, str) or relation_type not in valid_types:
      errors += [f'Relationship type "{relation_type}" is not a valid enum value']
    elif not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
      errors += [
        f'Relationship confidence "{confidence}" is not in [0.0, 1.0] for relationship "{subject}" -> "{relation_type}" -> "{obj}"'
      ]

  msg: str = f"[validate_graph] Checked {len(entities)} entities, {len(relationships)} relationships. Found {len(errors)} errors."
  return {
    "validation_errors": errors,
    "processing_log": state.get("processing_log", []) + [msg]
  }
