from backend_placeholder.state import KnowledgeExtractionState
from StudyOntology.lib import KnowledgeRelationship
from StudyOntology.lib import Concept
from StudyOntology.lib import Method
from StudyOntology.lib import Person
from StudyOntology.lib import Theory
from typing import Any

def inject_graph_schema_options(state: KnowledgeExtractionState) -> dict[str, Any]:
  options: dict[str, Any] = {
    "entity_types": ["Concept", "Theory", "Person", "Method"],
    "entity_schemas": {
      "Concept": Concept.model_json_schema(),
      "Theory": Theory.model_json_schema(),
      "Person": Person.model_json_schema(),
      "Method": Method.model_json_schema()
    },
    "relationship_schema": KnowledgeRelationship.model_json_schema()
  }
  msg: str = "[inject_graph_schema_options] Loaded JSON schema options for extraction."
  return {
    "graph_schema_options": options,
    "processing_log": state.get("processing_log", []) + [msg]
  }
