from .services.query_service import query_subgraph_by_relationship_type
from .services.query_service import query_subgraph_by_entity_types
from .services.query_service import query_subgraph_by_sources
from .services.query_service import query_subgraph_by_source
from .services.query_service import query_subgraph_by_entity
from .services.query_service import query_relationships
from .services.extract_service import run_extract
from .services.upload_service import ingest_upload
from .services.errors import ServiceError
from . import models
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile
from fastapi import HTTPException
from fastapi import FastAPI
from pydantic import ValidationError
from typing import NoReturn

APP: FastAPI = FastAPI()

APP.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["*"],
  allow_headers=["*"],
)


@APP.get("/")
def placeholder() -> dict[str, str]:
  return {"placeholder": "placeholder"}


def _raise_http_error(exc: ServiceError) -> NoReturn:
  raise HTTPException(
    status_code=exc.status_code,
    detail={
      "error_code": exc.error_code,
      "message": exc.message,
    },
  )


def _raise_validation_error(exc: ValidationError) -> NoReturn:
  raise HTTPException(
    status_code=422,
    detail={
      "error_code": "validation_error",
      "message": str(exc),
    },
  )


@APP.post("/upload", response_model=models.UploadResponse)
async def upload_endpoint(file: UploadFile) -> models.UploadResponse:
  try:
    return await ingest_upload(file)
  except ServiceError as exc:
    _raise_http_error(exc)


@APP.post("/extract", response_model=models.ExtractResponse)
def extract_endpoint(upload_request: models.ExtractRequest) -> models.ExtractResponse:
  try:
    return run_extract(upload_request)
  except ServiceError as exc:
    _raise_http_error(exc)


@APP.get("/query/relationships", response_model=models.RelationshipsQueryResponse)
def relationships_query_endpoint(
  limit: int = 100,
  offset: int = 0,
  min_confidence: float | None = None,
  max_confidence: float | None = None,
) -> models.RelationshipsQueryResponse:
  try:
    request = models.RelationshipsQueryRequest(
      limit=limit,
      offset=offset,
      min_confidence=min_confidence,
      max_confidence=max_confidence,
    )
    return query_relationships(request)
  except ValidationError as exc:
    _raise_validation_error(exc)


@APP.get("/query/subgraph/source/{source_id}", response_model=models.GraphSubgraphResponse)
def source_subgraph_endpoint(
  source_id: str,
  limit: int = 100,
  offset: int = 0,
) -> models.GraphSubgraphResponse:
  try:
    request = models.SourceSubgraphQueryRequest(limit=limit, offset=offset)
    return query_subgraph_by_source(source_id=source_id, request=request)
  except ValidationError as exc:
    _raise_validation_error(exc)


@APP.post("/query/subgraph/sources", response_model=models.GraphSubgraphResponse)
def sources_subgraph_endpoint(request: models.SourcesSubgraphRequest) -> models.GraphSubgraphResponse:
  return query_subgraph_by_sources(request)


@APP.get("/query/subgraph/entity/{entity_id_or_name}", response_model=models.GraphSubgraphResponse)
def entity_subgraph_endpoint(
  entity_id_or_name: str,
  limit: int = 100,
  offset: int = 0,
) -> models.GraphSubgraphResponse:
  try:
    request = models.EntitySubgraphQueryRequest(limit=limit, offset=offset)
    return query_subgraph_by_entity(entity_id_or_name=entity_id_or_name, request=request)
  except ValidationError as exc:
    _raise_validation_error(exc)


@APP.get("/query/relationships/type/{relationship_type}", response_model=models.GraphSubgraphResponse)
def relationship_type_subgraph_endpoint(
  relationship_type: str,
  limit: int = 100,
  offset: int = 0,
) -> models.GraphSubgraphResponse:
  try:
    request = models.RelationshipTypeSubgraphQueryRequest(
      relationship_type=relationship_type,
      limit=limit,
      offset=offset,
    )
    return query_subgraph_by_relationship_type(request)
  except ValidationError as exc:
    _raise_validation_error(exc)


@APP.post("/query/subgraph/entity-types", response_model=models.GraphSubgraphResponse)
def entity_types_subgraph_endpoint(request: models.EntityTypesSubgraphRequest) -> models.GraphSubgraphResponse:
  return query_subgraph_by_entity_types(request)
