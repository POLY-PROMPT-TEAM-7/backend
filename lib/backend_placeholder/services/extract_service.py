from .path_safety import validate_artifact_path
from .errors import ServiceError
from ..database import mark_artifact_processed
from ..database import get_processed_artifact
from ..database import count_relationships
from ..database import count_entities
from ..database import initialize_db
from ..database import add_data_to_db
from ..models import SourceSummary
from ..models import UploadArtifact
from ..models import ExtractResponse
from ..models import ExtractRequest
from ..agent import process_document
from StudyOntology.lib import DocumentOrigin
from StudyOntology.lib import SourceDocument


def run_extract(request: ExtractRequest) -> ExtractResponse:
  artifact_path = validate_artifact_path(request.artifact_path)
  if not artifact_path.exists() or not artifact_path.is_file():
    raise ServiceError(404, "artifact_not_found", "artifact file was not found")

  try:
    artifact = UploadArtifact.model_validate_json(artifact_path.read_text(encoding="utf-8"))
  except Exception as exc:
    raise ServiceError(400, "artifact_invalid", f"artifact JSON is invalid: {exc}") from exc

  initialize_db()
  processed = get_processed_artifact(str(artifact_path), artifact.artifact_sha256)
  if processed is not None:
    return ExtractResponse(
      artifact_path=str(artifact_path),
      artifact_sha256=artifact.artifact_sha256,
      already_processed=True,
      added_entities=0,
      added_relationships=0,
      sources=[SourceSummary(source_id=artifact.source_id, source_name=artifact.source_name)],
    )

  source_document = SourceDocument(
    id=artifact.source_id,
    name=artifact.source_name,
    origin=DocumentOrigin.USER_UPLOAD,
    file_path=str(artifact_path),
  )

  before_entities = count_entities()
  before_relationships = count_relationships()

  knowledge_graph = process_document(
    filename=artifact.source_name,
    extracted_text=artifact.extracted_text,
    source_document=source_document,
  )
  add_data_to_db(knowledge_graph)

  after_entities = count_entities()
  after_relationships = count_relationships()
  added_entities = max(0, after_entities - before_entities)
  added_relationships = max(0, after_relationships - before_relationships)

  mark_artifact_processed(
    artifact_path=str(artifact_path),
    artifact_sha256=artifact.artifact_sha256,
    source_id=artifact.source_id,
    source_name=artifact.source_name,
  )

  return ExtractResponse(
    artifact_path=str(artifact_path),
    artifact_sha256=artifact.artifact_sha256,
    already_processed=False,
    added_entities=added_entities,
    added_relationships=added_relationships,
    sources=[SourceSummary(source_id=artifact.source_id, source_name=artifact.source_name)],
  )
