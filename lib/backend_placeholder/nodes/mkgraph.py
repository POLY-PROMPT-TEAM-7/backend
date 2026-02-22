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


def _normalize_entity_id(value: Any) -> Any:
  if not isinstance(value, str):
    return value

  normalized: str = value.strip().lower().replace("_", "-")
  if normalized.startswith("theory:"):
    normalized = "concept:" + normalized.split(":", 1)[1]
  return normalized


def _coerce_entities(values: list[Any], klass: type[Any], class_name: str, id_prefix: str | None) -> list[Any]:
  result: list[Any] = []
  for value in values:
    payload: Any = None
    if isinstance(value, dict):
      payload = dict(value)
    elif hasattr(value, "model_dump"):
      try:
        payload = value.model_dump()
      except Exception:
        payload = None

    if isinstance(payload, dict):
      normalized_id = _normalize_entity_id(payload.get("id"))
      if isinstance(normalized_id, str):
        payload["id"] = normalized_id

      if id_prefix is not None:
        if not isinstance(normalized_id, str) or not normalized_id.startswith(id_prefix):
          continue

      try:
        result.append(klass(**payload))
      except Exception:
        continue
      continue

    if isinstance(value, klass):
      if id_prefix is None:
        result.append(value)
      else:
        normalized_id = _normalize_entity_id(getattr(value, "id", None))
        if isinstance(normalized_id, str) and normalized_id.startswith(id_prefix):
          result.append(value)
      continue

    if payload is None and value.__class__.__name__ != class_name:
      continue

  return result

def _coerce_relationships(values: list[Any]) -> tuple[list[KnowledgeRelationship], int]:
  result: list[KnowledgeRelationship] = []
  skipped_uncoercible: int = 0
  for value in values:
    payload: Any = None
    if isinstance(value, dict):
      payload = dict(value)
    elif hasattr(value, "model_dump"):
      try:
        payload = value.model_dump()
      except Exception:
        payload = None

    if not isinstance(payload, dict):
      skipped_uncoercible += 1
      continue

    normalized_subject = _normalize_entity_id(payload.get("subject"))
    normalized_object = _normalize_entity_id(payload.get("object"))
    if isinstance(normalized_subject, str):
      payload["subject"] = normalized_subject
    if isinstance(normalized_object, str):
      payload["object"] = normalized_object

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
  concepts: list[Concept] = _coerce_entities(entities, Concept, "Concept", "concept:")
  theories: list[Theory] = _coerce_entities(entities, Theory, "Theory", "theory:")
  persons: list[Person] = _coerce_entities(entities, Person, "Person", "person:")
  methods: list[Method] = _coerce_entities(entities, Method, "Method", "method:")
  entity_assignments: list[Assignment] = _coerce_entities(entities, Assignment, "Assignment", "assignment:")
  source_documents: list[SourceDocument] = _coerce_entities(entities, SourceDocument, "SourceDocument", None)

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
  skipped_self_reference: int = 0
  skipped_zero_confidence: int = 0
  skipped_duplicate: int = 0
  seen_relationships: set[tuple[str, str, str]] = set()
  for rel in relationship_models:
    if rel.subject == rel.object:
      skipped_self_reference += 1
      continue

    if rel.confidence is not None and float(rel.confidence) == 0.0:
      skipped_zero_confidence += 1
      continue

    if rel.subject not in entity_ids or rel.object not in entity_ids:
      skipped_missing_endpoint += 1
      continue

    predicate: str = rel.predicate if isinstance(rel.predicate, str) else (rel.predicate.value if hasattr(rel.predicate, "value") else str(rel.predicate))
    dedupe_key: tuple[str, str, str] = (rel.subject, predicate, rel.object)
    if dedupe_key in seen_relationships:
      skipped_duplicate += 1
      continue

    seen_relationships.add(dedupe_key)
    relationships.append(rel)

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
      f"skipped_missing_endpoint={skipped_missing_endpoint} skipped_uncoercible={skipped_uncoercible} "
      f"skipped_self_reference={skipped_self_reference} skipped_zero_confidence={skipped_zero_confidence} "
      f"skipped_duplicate={skipped_duplicate}"
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
