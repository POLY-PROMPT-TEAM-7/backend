from StudyOntology.lib import KnowledgeRelationship
from StudyOntology.lib import KnowledgeEntity
from pydantic import BaseModel

class ExtractedGraphPayload(BaseModel):
  entities: list[KnowledgeEntity]
  relationships: list[KnowledgeRelationship]