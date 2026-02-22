from StudyOntology.lib import KnowledgeEntity
from StudyOntology.lib import KnowledgeRelationship
from StudyOntology.lib import RelationshipType
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pathlib import Path
from typing import Any

DEFAULT_LIMIT: int = 100
MAX_LIMIT: int = 1000
MAX_SOURCE_IDS: int = 100
MAX_ENTITY_TYPES: int = 20

ALLOWED_ENTITY_TYPES: set[str] = {
  "Concept",
  "Theory",
  "Person",
  "Method",
  "Assignment",
}
ALLOWED_RELATIONSHIP_TYPES: set[str] = {
  rel_type.value if hasattr(rel_type, "value") else str(rel_type)
  for rel_type in RelationshipType
}

class ExtractedGraphPayload(BaseModel):
  entities: list[KnowledgeEntity]
  relationships: list[KnowledgeRelationship]

class ErrorEnvelope(BaseModel):
  error_code: str
  message: str

class SourceSummary(BaseModel):
  source_id: str
  source_name: str

class SourceRecord(BaseModel):
  source_id: str
  source_name: str
  data: dict[str, Any]

class EntityRecord(BaseModel):
  entity_id: str
  entity_name: str
  entity_type: str
  data: dict[str, Any]

class RelationshipRecord(BaseModel):
  subject_entity_id: str
  object_entity_id: str
  relationship_type: str
  confidence: float | None = None
  data: dict[str, Any]

class UploadResponse(BaseModel):
  source_id: str
  source_name: str
  artifact_path: str
  artifact_sha256: str
  metadata_status: str
  metadata_error_code: str | None = None
  metadata_error_message: str | None = None
  compressed_bytes: int
  decompressed_bytes: int

class ExtractRequest(BaseModel):
  artifact_path: Path
  query_canvas: bool = False
  query_openalex: bool = False

class ExtractResponse(BaseModel):
  artifact_path: str
  artifact_sha256: str
  already_processed: bool
  added_entities: int
  added_relationships: int
  sources: list[SourceSummary]

class QueryPaging(BaseModel):
  limit: int = Field(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT)
  offset: int = Field(default=0, ge=0)

class RelationshipsQueryRequest(QueryPaging):
  min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
  max_confidence: float | None = Field(default=None, ge=0.0, le=1.0)

  @model_validator(mode="after")
  def validate_confidence_window(self) -> "RelationshipsQueryRequest":
    if (
      self.min_confidence is not None
      and self.max_confidence is not None
      and self.min_confidence > self.max_confidence
    ):
      raise ValueError("min_confidence must be <= max_confidence")
    return self

class RelationshipsQueryResponse(BaseModel):
  items: list[RelationshipRecord]
  total: int
  limit: int
  offset: int

class SourceSubgraphQueryRequest(QueryPaging):
  pass

class SourcesSubgraphRequest(QueryPaging):
  source_ids: list[str] = Field(min_length=1, max_length=MAX_SOURCE_IDS)

  @field_validator("source_ids")
  @classmethod
  def validate_source_ids(cls, value: list[str]) -> list[str]:
    cleaned = [x.strip() for x in value if x.strip()]
    if not cleaned:
      raise ValueError("source_ids must include at least one non-empty source id")
    return cleaned

class EntitySubgraphQueryRequest(QueryPaging):
  pass

class RelationshipTypeSubgraphQueryRequest(QueryPaging):
  relationship_type: str

  @field_validator("relationship_type")
  @classmethod
  def validate_relationship_type(cls, value: str) -> str:
    if value not in ALLOWED_RELATIONSHIP_TYPES:
      allowed = ", ".join(sorted(ALLOWED_RELATIONSHIP_TYPES))
      raise ValueError(f"relationship_type must be one of: {allowed}")
    return value

class EntityTypesSubgraphRequest(QueryPaging):
  entity_types: list[str] = Field(min_length=1, max_length=MAX_ENTITY_TYPES)

  @field_validator("entity_types")
  @classmethod
  def validate_entity_types(cls, value: list[str]) -> list[str]:
    cleaned = [x.strip() for x in value if x.strip()]
    if not cleaned:
      raise ValueError("entity_types must include at least one non-empty type")
    invalid = [x for x in cleaned if x not in ALLOWED_ENTITY_TYPES]
    if invalid:
      allowed = ", ".join(sorted(ALLOWED_ENTITY_TYPES))
      raise ValueError(f"entity_types contains invalid values: {invalid}. allowed: {allowed}")
    return cleaned

class GraphSubgraphResponse(BaseModel):
  entities: list[EntityRecord]
  relationships: list[RelationshipRecord]
  sources: list[SourceRecord]
  total_entities: int
  total_relationships: int
  total_sources: int
  limit: int
  offset: int

class UploadArtifact(BaseModel):
  source_id: str
  source_name: str
  original_filename: str
  extracted_text: str
  artifact_sha256: str
  metadata_status: str
  metadata_error_code: str | None = None
  metadata_error_message: str | None = None
  compressed_bytes: int
  decompressed_bytes: int
  created_at: str

class TextractAdapterResult(BaseModel):
  text: str
  metadata_status: str
  error_code: str | None = None
  error_message: str | None = None
