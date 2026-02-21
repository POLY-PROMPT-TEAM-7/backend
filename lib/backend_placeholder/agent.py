from __future__ import annotations

import os
from typing import Any, Optional, TypedDict, cast

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, SecretStr

from StudyOntology.lib import KnowledgeEntity, KnowledgeRelationship, SourceDocument
from backend_placeholder.nodes.enrich_openalex import enrich_with_openalex
from backend_placeholder.nodes.mkgraph import mkgraph
from backend_placeholder.nodes.retry_flow import route_after_validate
from backend_placeholder.nodes.schema_options import inject_graph_schema_options
from backend_placeholder.nodes.validate_graph import validate_graph
from backend_placeholder.state import KnowledgeExtractionState
from backend_placeholder.nodes.mkgraph import mkgraph
from StudyOntology.lib import SourceDocument
from langgraph.graph import StateGraph
from langgraph.graph import START
from langgraph.graph import END
from typing import Any

def build_pipeline() -> Any:
  graph: StateGraph = StateGraph(KnowledgeExtractionState)

  graph.add_node("inject_schema_options", inject_graph_schema_options)
  graph.add_node("extract_graph", extract_graph)
  graph.add_node("validate_graph", validate_graph)
  graph.add_node("retry_extract_graph", retry_extract_graph)
  graph.add_node("mkgraph", mkgraph)
  graph.add_node("enrich_with_openalex", enrich_with_openalex)

  graph.add_edge(START, "inject_schema_options")
  graph.add_edge("inject_schema_options", "extract_graph")
  graph.add_edge("extract_graph", "validate_graph")
  graph.add_conditional_edges("validate_graph", route_after_validate, {
    "retry": "retry_extract_graph",
    "done": "mkgraph",
  })
  graph.add_edge("retry_extract_graph", "validate_graph")
  graph.add_edge("mkgraph", "enrich_with_openalex")
  graph.add_edge("enrich_with_openalex", END)

  return graph.compile()


pipeline: Any = build_pipeline()


def process_document(
  filename: str,
  extracted_text: str,
  source_document: Optional[SourceDocument] = None,
) -> KnowledgeExtractionState:
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
    "processing_log": [f"Started processing: {filename}"],
    "enriched_entities": [],
    "enriched_relationships": [],
  }
  return pipeline.invoke(initial_state)


class MCPToolSpec(TypedDict):
  name: str
  description: str
  input_schema: dict[str, Any]


def get_schema_options_tool() -> MCPToolSpec:
  return {
    "name": "get_graph_schema_options",
    "description": "Return JSON schema options for graph entities and relationships.",
    "input_schema": {
      "type": "object",
      "properties": {},
      "additionalProperties": False,
    },
  }