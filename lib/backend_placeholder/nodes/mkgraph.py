from backend_placeholder.state import KnowledgeExtractionState
from StudyOntology.lib import KnowledgeRelationship
from StudyOntology.lib import KnowledgeEntity
from StudyOntology.lib import KnowledgeGraph
from StudyOntology.lib import Method
from StudyOntology.lib import Person
from StudyOntology.lib import Theory
from StudyOntology.lib import Concept
from typing import Any


def mkgraph(state: KnowledgeExtractionState) -> dict[str, Any]:
  entities: list[KnowledgeEntity] = state.get("raw_entities", [])
  relationships: list[KnowledgeRelationship] = state.get("raw_relationships", [])

  concepts: list[Concept] = [x for x in entities if isinstance(x, Concept)]
  theories: list[Theory] = [x for x in entities if isinstance(x, Theory)]
  persons: list[Person] = [x for x in entities if isinstance(x, Person)]
  methods: list[Method] = [x for x in entities if isinstance(x, Method)]

  graph_model: Any = KnowledgeGraph
  graph_object: Any = graph_model(
    concepts=concepts,
    theories=theories,
    persons=persons,
    methods=methods,
    relationships=relationships
  )

  try:
    serialized_graph: dict[str, Any] = graph_object.as_json()
    msg: str = f"[mkgraph] Built KnowledgeGraph with {len(entities)} entities, {len(relationships)} relationships"
    return {
      "knowledge_graph": serialized_graph,
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
