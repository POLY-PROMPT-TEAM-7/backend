from backend_placeholder.nodes.schema_options import inject_graph_schema_options
from backend_placeholder.nodes.extract_graph import retry_extract_graph
from backend_placeholder.nodes.retry_flow import route_after_validate
from backend_placeholder.nodes.validate_graph import validate_graph
from backend_placeholder.nodes.extract_graph import extract_graph
from backend_placeholder.nodes.link_canvas import link_canvas_assignments
from backend_placeholder.integrations.enrich_openalex import enrich_with_openalex
from backend_placeholder.integrations.canvas import canvas_node
from backend_placeholder.state import KnowledgeExtractionState
from backend_placeholder.nodes.mkgraph import mkgraph
from StudyOntology.lib import KnowledgeGraph
from StudyOntology.lib import SourceDocument
from langgraph.graph import StateGraph
from langgraph.graph import START
from langgraph.graph import END
from typing import cast
from typing import Any
from typing import Literal

def openalex_gate(state: KnowledgeExtractionState) -> dict[str, Any]:
  return {}

def canvas_node_typed(state: KnowledgeExtractionState) -> dict[str, Any]:
  return canvas_node(cast(dict[str, Any], state))

def route_after_extraction(state: KnowledgeExtractionState) -> Literal["openalex", "check_canvas_links"]:
  if state.get("query_openalex", False):
    return "openalex"
  return "check_canvas_links"

def route_after_enrichment(state: KnowledgeExtractionState) -> Literal["link_canvas", "skip_canvas_link"]:
  has_assignments: bool = len(state.get("canvas_assignments", [])) > 0
  if has_assignments:
    return "link_canvas"
  return "skip_canvas_link"

def build_pipeline() -> Any:
  """Build the knowledge extraction pipeline.

  Flow:
    START
      -> inject_schema_options
      -> extract_graph + canvas_node
      -> validate_graph
      -> retry | fail | done
  """
  graph: StateGraph = StateGraph(KnowledgeExtractionState)

  graph.add_node("inject_schema_options", inject_graph_schema_options)
  graph.add_node("canvas_node", canvas_node_typed)
  graph.add_node("extract_graph", extract_graph)
  graph.add_node("validate_graph", validate_graph)
  graph.add_node("retry_extract_graph", retry_extract_graph)
  graph.add_node("openalex_gate", openalex_gate)
  graph.add_node("enrich_with_openalex", enrich_with_openalex)
  graph.add_node("link_canvas_assignments", link_canvas_assignments)
  graph.add_node("mkgraph", mkgraph)

  graph.add_edge(START, "inject_schema_options")
  graph.add_edge("inject_schema_options", "canvas_node")
  graph.add_edge("inject_schema_options", "extract_graph")
  graph.add_edge("canvas_node", "validate_graph")
  graph.add_edge("extract_graph", "validate_graph")

  # given validation result, when routing, then retry/fail/done branch selected
  graph.add_conditional_edges("validate_graph", route_after_validate, {
    "retry": "retry_extract_graph",
    "fail": "mkgraph",
    "done": "openalex_gate"
  })

  # given openalex flag, when routing after extraction, then enrich or skip
  graph.add_conditional_edges("openalex_gate", route_after_extraction, {
    "openalex": "enrich_with_openalex",
    "check_canvas_links": "link_canvas_assignments"
  })

  # given assignment presence, when routing after enrichment, then link or skip
  graph.add_conditional_edges("enrich_with_openalex", route_after_enrichment, {
    "link_canvas": "link_canvas_assignments",
    "skip_canvas_link": "mkgraph"
  })

  graph.add_edge("retry_extract_graph", "validate_graph")
  graph.add_edge("link_canvas_assignments", "mkgraph")
  graph.add_edge("mkgraph", END)

  return graph.compile()

PIPELINE: Any = build_pipeline()

def process_document(
  filename: str,
  extracted_text: str,
  query_canvas: bool = False,
  query_openalex: bool = False,
  source_document: SourceDocument | None = None
) -> KnowledgeGraph:
  # Pipeline entry point - returns Pydantic KnowledgeGraph
  """Run the full extraction pipeline on a document."""
  initial_state: dict[str, Any] = {
    "filename": filename,
    "document_type": "",
    "extracted_text": extracted_text,
    "query_canvas": query_canvas,
    "query_openalex": query_openalex,
    "source_document": source_document,
    "chunks": [],
    "raw_entities": [],
    "raw_relationships": [],
    "enriched_entities": [],
    "enriched_relationships": [],
    "canvas_courses": [],
    "canvas_assignments": [],
    "validation_errors": [],
    "retry_count": 0,
    "knowledge_graph": None,
    "graph_stats": {},
    "graph_schema_options": {},
    "processing_log": [f"Started processing: {filename}"]
  }
  result: KnowledgeExtractionState = cast(KnowledgeExtractionState, PIPELINE.invoke(initial_state))
  knowledge_graph: KnowledgeGraph | None = cast(KnowledgeGraph | None, result["knowledge_graph"])
  if knowledge_graph is None:
    return KnowledgeGraph(
      concepts=[],
      theories=[],
      persons=[],
      methods=[],
      assignments=[],
      relationships=[],
      source_documents=[]
    )
  return knowledge_graph
