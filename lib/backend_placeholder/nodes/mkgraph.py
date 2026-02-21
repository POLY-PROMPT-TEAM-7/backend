from backend_placeholder.state import KnowledgeExtractionState
from StudyOntology.lib import KnowledgeRelationship
from StudyOntology.lib import KnowledgeEntity
from StudyOntology.lib import KnowledgeGraph
from StudyOntology.lib import SourceDocument
from StudyOntology.lib import Concept
from StudyOntology.lib import Theory
from StudyOntology.lib import Person
from StudyOntology.lib import Method
from typing import Any

def mkgraph(state: KnowledgeExtractionState) -> dict[str, Any]:
  """
  Build a KnowledgeGraph from the validated entities and relationships in state.

  Sorts entities into typed lists (concepts, theories, persons, methods),
  attaches relationships and source documents, then validates the full graph.
  """
  source: SourceDocument = state["source_document"]

  entities: list[KnowledgeEntity] = state.get("entities", [])
  relationships: list[KnowledgeRelationship] = state.get("raw_relationships", [])

  concepts: list[Concept] = [x for x in entities if isinstance(x, Concept)]
  theories: list[Theory] = [x for x in entities if isinstance(x, Theory)]
  persons: list[Person] = [x for x in entities if isinstance(x, Person)]
  methods: list[Method] = [x for x in entities if isinstance(x, Method)]

  kg: KnowledgeGraph = KnowledgeGraph(
    source=source,
    concepts=concepts,
    theories=theories,
    persons=persons,
    methods=methods,
    relationships=relationships
  )

  try:
    as_json: dict[str, Any] = kg.as_json()
    KnowledgeGraph.model_validate_json(as_json)
    msg: str = f"[mkgraph] Built KnowledgeGraph with {len(entities)} entities, {len(relationships)} relationships"
    return {"knowledge_graph": as_json, "validation_errors": [], "processing_log": state.get("processing_log", []) + [msg]}
  except Exception as e:
    msg = f"[mkgraph] Final validation failed: {e}"
    return {"knowledge_graph": None, "validation_errors": [str(e)], "processing_log": state.get("processing_log", []) + [msg]}
