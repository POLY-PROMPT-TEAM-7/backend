from backend_placeholder.nodes.schema_options import inject_graph_schema_options
from backend_placeholder.nodes.extract_graph import retry_extract_graph
from backend_placeholder.nodes.retry_flow import route_after_validate
from backend_placeholder.nodes.validate_graph import validate_graph
from backend_placeholder.nodes.extract_graph import extract_graph
from backend_placeholder.state import KnowledgeExtractionState
from backend_placeholder.nodes.mkgraph import mkgraph
from StudyOntology.lib import SourceDocument
from langgrapgh.graph import StateGraph
from langgraph.graph import START
from langgraph.graph import END
from typing import Any

def build_pipeline() -> Any:
  """Build the knowledge extraction pipeline.

  Flow:
    inject_schema_options
      -> extract_graph
        -> validate_graph
          -> (retry?) retry_extract_graph -> validate_graph
          -> (done)  mkgraph -> END
  """
  graph: StateGraph = StateGraph(KnowledgeExtractionState)

  graph.add_node("inject_schema_options", inject_graph_schema_options)
  graph.add_node("extract_graph", extract_graph)
  graph.add_node("validate_graph", validate_graph)
  graph.add_node("retry_extract_graph", retry_extract_graph)
  graph.add_node("mkgraph", mkgraph)

  graph.add_edge(START, "inject_schema_options")
  graph.add_edge("inject_schema_options", "extract_graph")
  graph.add_edge("extract_graph", "validate_graph")
  graph.add_conditional_edges("validate_graph", route_after_validate, {
    "retry": "retry_extract_graph",
    "done": "mkgraph"
  })
  graph.add_edge("retry_extract_graph", "validate_graph")
  graph.add_edge("mkgraph", END)

  return graph.compile()

PIPELINE: Any = build_pipeline()

def process_document(
  filename: str,
  extracted_text: str,
  source_document: SourceDocument | None = None
) -> KnowledgeExtractionState:
  """Run the full extraction pipeline on a document."""
  initial_state: KnowledgeExtractionState = {
    "filename": filename,
    "document_type": "",
    "textracted_text": extracted_text,
    "source_document": source_document,
    "chunks": [],
    "raw_entities": [],
    "raw_relationships": [],
    "validation_errors": [],
    "retry_count": 0,
    "knowledge_graph": None,
    "graph_stats": {},
    "graph_schema_options": {},
    "processing_log": [f"Started processing: {filename}"]
  }
  return PIPELINE.invoke(initial_state)