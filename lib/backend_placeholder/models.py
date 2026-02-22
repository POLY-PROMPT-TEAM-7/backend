from StudyOntology.lib import KnowledgeRelationship
from StudyOntology.lib import KnowledgeEntity
from pydantic import BaseModel
from pathlib import Path

class ExtractedGraphPayload(BaseModel):
  entities: list[KnowledgeEntity]
  relationships: list[KnowledgeRelationship]

class SourceRecord(BaseModel):
  source_id: int
  source_name: str
  text: str

class ExtractResponse(BaseModel):
    source_id: int
    source_name: str

class ExtractRequest(BaseModel):
  text_path: str
