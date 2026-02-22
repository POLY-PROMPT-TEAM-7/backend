from backend_placeholder.state import KnowledgeExtractionState
from StudyOntology.lib import Assignment
from StudyOntology.lib import Concept
from StudyOntology.lib import KnowledgeEntity
from StudyOntology.lib import KnowledgeGraph
from StudyOntology.lib import KnowledgeRelationship
from StudyOntology.lib import Method
from StudyOntology.lib import Person
from StudyOntology.lib import SourceDocument
from StudyOntology.lib import Theory
from typing import Any


def _coerce_entities(values: list[Any], klass: type[Any], class_name: str) -> list[Any]:
  result: list[Any] = []
  for value in values:
    if isinstance(value, klass):
      result.append(value)
      continue

    payload: Any = None
    if isinstance(value, dict):
      payload = value
    elif hasattr(value, "model_dump"):
      try:
        payload = value.model_dump()
      except Exception:
        payload = None

    if payload is None and value.__class__.__name__ != class_name:
      continue

    if not isinstance(payload, dict):
      continue
    try:
      result.append(klass(**payload))
    except Exception:
      continue
  return result

def _coerce_relationships(values: list[Any]) -> tuple[list[KnowledgeRelationship], int]:
  result: list[KnowledgeRelationship] = []
  skipped_uncoercible: int = 0
  for value in values:
    if isinstance(value, KnowledgeRelationship):
      result.append(value)
      continue

    payload: Any = None
    if isinstance(value, dict):
      payload = value
    elif hasattr(value, "model_dump"):
      try:
        payload = value.model_dump()
      except Exception:
        payload = None

    if not isinstance(payload, dict):
      skipped_uncoercible += 1
      continue

    try:
      result.append(KnowledgeRelationship(**payload))
    except Exception:
      skipped_uncoercible += 1
      continue

  return result, skipped_uncoercible

def mkgraph(state: KnowledgeExtractionState) -> dict[str, Any]:
  entities: list[KnowledgeEntity] = state.get("raw_entities", [])
  raw_relationships: list[Any] = state.get("raw_relationships", [])
  state_assignments: list[Any] = state.get("canvas_assignments", [])
  state_source_document: Any = state.get("source_document", None)

  # Build complete KnowledgeGraph with all StudyOntology entity types
  concepts: list[Concept] = _coerce_entities(entities, Concept, "Concept")
  theories: list[Theory] = _coerce_entities(entities, Theory, "Theory")
  persons: list[Person] = _coerce_entities(entities, Person, "Person")
  methods: list[Method] = _coerce_entities(entities, Method, "Method")
  entity_assignments: list[Assignment] = _coerce_entities(entities, Assignment, "Assignment")
  source_documents: list[SourceDocument] = _coerce_entities(entities, SourceDocument, "SourceDocument")

  assignment_models: list[Assignment] = []
  for x in state_assignments:
    if isinstance(x, Assignment):
      assignment_models.append(x)
    elif isinstance(x, dict):
      try:
        assignment_models.append(Assignment(**x))
      except Exception:
        continue
  assignment_by_id: dict[str, Assignment] = {x.id: x for x in entity_assignments + assignment_models}

  if isinstance(state_source_document, SourceDocument):
    source_documents = source_documents + [state_source_document]

  entity_ids: set[str] = set(x.id for x in concepts + theories + persons + methods)
  entity_ids.update(assignment_by_id.keys())
  entity_ids.update(x.id for x in source_documents)

  relationship_models, skipped_uncoercible = _coerce_relationships(raw_relationships)
  relationships: list[KnowledgeRelationship] = []
  skipped_missing_endpoint: int = 0
  for rel in relationship_models:
    if rel.subject in entity_ids and rel.object in entity_ids:
      relationships.append(rel)
    else:
      skipped_missing_endpoint += 1

  graph_object: KnowledgeGraph = KnowledgeGraph(
    concepts=concepts,
    theories=theories,
    persons=persons,
    methods=methods,
    assignments=list(assignment_by_id.values()),
    relationships=relationships,
    source_documents=source_documents
  )

  try:
    msg: str = (
      "[mkgraph] Built KnowledgeGraph "
      f"raw_entities={len(entities)} materialized_entities={len(entity_ids)} "
      f"raw_relationships={len(raw_relationships)} kept_relationships={len(relationships)} "
      f"skipped_missing_endpoint={skipped_missing_endpoint} skipped_uncoercible={skipped_uncoercible}"
    )
    print(msg)
    return {
      "knowledge_graph": graph_object,
      "validation_errors": [],
      "processing_log": state.get("processing_log", []) + [msg]
    }
  except Exception as e:
    msg = f"[mkgraph] Final serialization failed: {e}"
    return {
      "knowledge_graph": None,
      "validation_errors": [str(e)],
      "processing_log": state.get("processing_log", []) + [msg]
    }
