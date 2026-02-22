from StudyOntology.lib import KnowledgeRelationship
from StudyOntology.lib import KnowledgeEntity
from pydantic import BaseModel

class ExtractedGraphPayload(BaseModel):
  entities: list[KnowledgeEntity]
  relationships: list[KnowledgeRelationship]

class UploadResponse(BaseModel):
  text_path: str

class ExtractResponse(BaseModel):
    source_id: int
    source_name: str

class UploadRequest(BaseModel):
  file_path: str
  content: str