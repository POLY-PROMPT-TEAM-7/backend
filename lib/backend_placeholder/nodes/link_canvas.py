from backend_placeholder.state import KnowledgeExtractionState
from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage
from StudyOntology.lib import Assignment
from StudyOntology.lib import KnowledgeEntity
from StudyOntology.lib import KnowledgeRelationship
from StudyOntology.lib import RelationshipType
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from pydantic import SecretStr
from typing import Any
from typing import Optional
from typing import cast
import os

class CanvasLinkPayload(BaseModel):
  relationships: list[KnowledgeRelationship]

def get_llm() -> Optional[ChatOpenAI]:
  api_key: str = os.getenv("OPENAI_API_KEY", "")
  if api_key == "":
    return None
  return ChatOpenAI(model="gpt-5.2", api_key=SecretStr(api_key))

def normalize_assignments(items: list[Any]) -> list[Assignment]:
  assignments: list[Assignment] = []
  for item in items:
    if isinstance(item, Assignment):
      assignments.append(item)
      continue
    if isinstance(item, dict):
      try:
        assignments.append(Assignment(**item))
      except Exception:
        continue
  return assignments

def build_linking_prompt(assignments: list[Assignment], entities: list[KnowledgeEntity]) -> str:
  assignment_view: list[dict[str, str]] = [
    {
      "id": x.id,
      "name": x.name,
      "description": x.description or ""
    }
    for x in assignments
  ]
  entity_view: list[dict[str, str]] = [
    {
      "id": x.id,
      "name": x.name,
      "type": x.__class__.__name__
    }
    for x in entities
  ]
  return (
    "Link assignments to extracted concepts/theories/methods using only existing IDs. "
    "Allowed predicates are COVERS or ASSESSED_BY only. "
    "Do not create new entities. Return only supported relationships with confidence in [0,1]. "
    f"Assignments: {assignment_view}. "
    f"Entities: {entity_view}."
  )

def link_canvas_assignments(state: KnowledgeExtractionState) -> dict[str, Any]:
  # 2nd LLM pass: link Canvas assignments to extracted concepts
  assignments: list[Assignment] = normalize_assignments(state.get("canvas_assignments", []))
  if len(assignments) == 0:
    return {
      "raw_relationships": state.get("raw_relationships", []),
      "processing_log": state.get("processing_log", [])
    }

  llm: Optional[ChatOpenAI] = get_llm()
  if llm is None:
    return {
      "raw_relationships": state.get("raw_relationships", []),
      "processing_log": state.get("processing_log", [])
    }

  raw_entities: list[KnowledgeEntity] = state.get("raw_entities", [])
  raw_relationships: list[KnowledgeRelationship] = state.get("raw_relationships", [])
  extractor = llm.with_structured_output(CanvasLinkPayload)
  try:
    result = cast(
      CanvasLinkPayload,
      extractor.invoke([
        SystemMessage(content="You are an expert at educational knowledge graph linking."),
        HumanMessage(content=build_linking_prompt(assignments, raw_entities))
      ])
    )
  except Exception:
    return {
      "raw_relationships": raw_relationships,
      "processing_log": state.get("processing_log", [])
    }

  entity_ids: set[str] = {x.id for x in raw_entities}
  assignment_ids: set[str] = {x.id for x in assignments}
  valid_ids: set[str] = entity_ids | assignment_ids
  allowed_predicates: set[str] = {RelationshipType.COVERS.value, RelationshipType.ASSESSED_BY.value}
  linked: list[KnowledgeRelationship] = [
    x for x in result.relationships
    if (
      x.predicate in allowed_predicates
      and x.subject in valid_ids
      and x.object in valid_ids
      and ((x.subject in assignment_ids and x.object in entity_ids) or (x.subject in entity_ids and x.object in assignment_ids))
    )
  ]
  return {
    "raw_relationships": raw_relationships + linked,
    "processing_log": state.get("processing_log", [])
  }
