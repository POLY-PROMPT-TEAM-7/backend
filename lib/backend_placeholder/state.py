from StudyOntology.lib import KnowledgeRelationship
from StudyOntology.lib import KnowledgeEntity
from StudyOntology.lib import SourceDocument
from typing import TypedDict
from typing import Optional
from typing import Any

class KnowledgeExtractionState(TypedDict):
  filename: str
  document_type: str
  textracted_text: str

  source_document: Optional[SourceDocument]
  chunks: list[str]
  raw_entities: list[KnowledgeEntity]
  raw_relationships: list[KnowledgeRelationship]

  validation_errors: list[str]
  retry_count: int

  knowledge_graph: Optional[dict[str, Any]]
  graph_stats: dict[str, Any]
  graph_schema_options: dict[str, Any]

  processing_log: list[str]
