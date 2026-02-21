from backend_placeholder.state import KnowledgeExtractionState
from backend_placeholder.models import ExtractedGraphPayload
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from typing import cast
from typing import Any
import os

load_dotenv()

LLM: ChatOpenAI = ChatOpenAI(model="gpt-4o", api_key=os.environ["OPENAI_API_KEY"])

def build_extraction_prompt(schema_options: dict[str, Any]) -> str:
  return f"Extract a clean knowledge graph from this document text. Return only entities and relationships that fit the allowed schema. Schema options: {schema_options}" 

def build_retry_prompt(
  validation_errors: list[str],
  schema_options: dict[str, Any]
) -> str:
  return f"Retry extraction and fix issues based on validation errors. Validation errors: {validation_errors}. Use this schema options object: {schema_options}"

def extract_graph(state: KnowledgeExtractionState) -> dict[str, Any]:
  schema_options: dict[str, Any] = state.get("graph_schema_options", {})
  extractor = LLM.with_structured_output(ExtractedGraphPayload)
  result = cast(
    ExtractedGraphPayload,
    extractor.invoke([
      SystemMessage(content=build_extraction_prompt(schema_options)),
      HumanMessage(content=state["textracted_text"])
    ])
  )
  entity_count = len(result.entities)
  rel_count = len(result.relationships)
  msg = f"[extract_graph] Extracted {entity_count} entities and {rel_count} relationships."
  return {
    "raw_entities": result.entities,
    "raw_relationships": result.relationships,
    "processing_log": state.get("processing_log", []) + [msg]
  }

def retry_extract_graph(state: KnowledgeExtractionState) -> dict[str, Any]:
  schema_options: dict[str, Any] = state.get("graph_schema_options", {})
  validation_errors: list[str] = state.get("validation_errors", [])
  extractor = LLM.with_structured_output(ExtractedGraphPayload)
  result = cast(
    ExtractedGraphPayload,
    extractor.invoke([
      SystemMessage(content=build_retry_prompt(validation_errors, schema_options)),
      HumanMessage(content=state["textracted_text"])
    ])
  )
  next_retry_count: int = state.get("retry_count", 0) + 1
  msg = f"[retry_extract_graph] Retry {next_retry_count} completed."
  return {
    "raw_entities": result.entities,
    "raw_relationships": result.relationships,
    "retry_count": next_retry_count,
    "validation_errors": [],
    "processing_log": state.get("processing_log", []) + [msg]
  }
