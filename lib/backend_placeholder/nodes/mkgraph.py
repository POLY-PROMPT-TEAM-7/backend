from backend_placeholder.state import KnowledgeExtractionState
from StudyOntology.lib import KnowledgeRelationship
from StudyOntology.lib import KnowledgeEntity
from StudyOntology.lib import KnowledgeGraph
from StudyOntology.lib import SourceDocument
from StudyOntology.lib import Assignment
from StudyOntology.lib import Method
from StudyOntology.lib import Person
from StudyOntology.lib import Theory
from StudyOntology.lib import Concept
from typing import Any

def mkgraph(state: KnowledgeExtractionState) -> dict[str, Any]:
  entities: list[KnowledgeEntity] = state.get("raw_entities", [])
  relationships: list[KnowledgeRelationship] = state.get("raw_relationships", [])
  state_assignments: list[Any] = state.get("canvas_assignments", [])
  state_source_document: Any = state.get("source_document", None)

  # Build complete KnowledgeGraph with all StudyOntology entity types
  concepts: list[Concept] = [x for x in entities if isinstance(x, Concept)]
  theories: list[Theory] = [x for x in entities if isinstance(x, Theory)]
  persons: list[Person] = [x for x in entities if isinstance(x, Person)]
  methods: list[Method] = [x for x in entities if isinstance(x, Method)]
  entity_assignments: list[Assignment] = [x for x in entities if isinstance(x, Assignment)]
  source_documents: list[SourceDocument] = [x for x in entities if isinstance(x, SourceDocument)]

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
    msg: str = f"[mkgraph] Built KnowledgeGraph with {len(entities)} entities, {len(relationships)} relationships"
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
