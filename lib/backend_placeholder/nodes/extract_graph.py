from backend_placeholder.state import KnowledgeExtractionState
from backend_placeholder.models import ExtractedGraphPayload
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
from StudyOntology.lib import RelationshipType
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from typing import Optional
from typing import cast
from typing import Any
import os

# Precanned expert extraction prompt - not user-configurable

def get_llm() -> Optional[ChatOpenAI]:
  api_key: str = os.getenv("OPENAI_API_KEY", "")
  if api_key == "":
    return None
  return ChatOpenAI(model="gpt-4o", api_key=SecretStr(api_key))

def build_extraction_prompt(schema_options: dict[str, Any]) -> str:
  relationship_values: str = ", ".join(x.value for x in RelationshipType)
  return (
    "You are an expert academic knowledge graph extractor. "
    "Extract only high-confidence entities and relationships directly supported by the document. "
    "Entity types allowed: Concept, Theory, Person, Method, Assignment. "
    "Relationship predicates must be exactly one of: "
    f"{relationship_values}. "
    "Return structured output matching the provided schemas. "
    "Use precise IDs and names, avoid hallucinations, and include provenance/confidence as required by schema. "
    "Schema options: "
    f"{schema_options}"
  )

def build_retry_prompt(
  validation_errors: list[str],
  schema_options: dict[str, Any]
) -> str:
  return f"Retry extraction and fix issues based on validation errors. Validation errors: {validation_errors}. Use this schema options object: {schema_options}"

def extract_graph(state: KnowledgeExtractionState) -> dict[str, Any]:
  schema_options: dict[str, Any] = state.get("graph_schema_options", {})
  llm: Optional[ChatOpenAI] = get_llm()
  if llm is None:
    return {
      "raw_entities": [],
      "raw_relationships": [],
      "validation_errors": ["OPENAI_API_KEY missing"],
      "processing_log": state.get("processing_log", [])
    }
  extractor = llm.with_structured_output(ExtractedGraphPayload)
  try:
    result = cast(
      ExtractedGraphPayload,
      extractor.invoke([
        SystemMessage(content=build_extraction_prompt(schema_options)),
        HumanMessage(content=state.get("extracted_text", ""))
      ])
    )
  except Exception as e:
    return {
      "raw_entities": state.get("raw_entities", []),
      "raw_relationships": state.get("raw_relationships", []),
      "validation_errors": [f"extract_graph failed: {e}"],
      "processing_log": state.get("processing_log", [])
    }
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
  llm: Optional[ChatOpenAI] = get_llm()
  next_retry_count: int = state.get("retry_count", 0) + 1
  if llm is None:
    return {
      "retry_count": next_retry_count,
      "validation_errors": ["OPENAI_API_KEY missing"],
      "processing_log": state.get("processing_log", [])
    }
  extractor = llm.with_structured_output(ExtractedGraphPayload)
  try:
    result = cast(
      ExtractedGraphPayload,
      extractor.invoke([
        SystemMessage(content=build_retry_prompt(validation_errors, schema_options)),
        HumanMessage(content=state.get("extracted_text", ""))
      ])
    )
  except Exception as e:
    return {
      "retry_count": next_retry_count,
      "validation_errors": [f"retry_extract_graph failed: {e}"],
      "processing_log": state.get("processing_log", [])
    }
  msg = f"[retry_extract_graph] Retry {next_retry_count} completed."
  return {
    "raw_entities": result.entities,
    "raw_relationships": result.relationships,
    "retry_count": next_retry_count,
    "validation_errors": [],
    "processing_log": state.get("processing_log", []) + [msg]
  }
