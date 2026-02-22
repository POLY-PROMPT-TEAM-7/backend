from ..database import get_subgraph_by_entity_types
from ..database import get_subgraph_by_source_ids
from ..database import get_subgraph_by_source_id
from ..database import get_subgraph_by_entity
from ..database import get_subgraph_by_relationship_type
from ..database import list_relationships_by_confidence
from ..models import GraphSubgraphResponse
from ..models import EntityTypesSubgraphRequest
from ..models import RelationshipsQueryResponse
from ..models import RelationshipsQueryRequest
from ..models import SourcesSubgraphRequest
from ..models import SourceSubgraphQueryRequest
from ..models import EntitySubgraphQueryRequest
from ..models import RelationshipTypeSubgraphQueryRequest


def query_relationships(request: RelationshipsQueryRequest) -> RelationshipsQueryResponse:
  items, total = list_relationships_by_confidence(
    limit=request.limit,
    offset=request.offset,
    min_confidence=request.min_confidence,
    max_confidence=request.max_confidence,
  )
  return RelationshipsQueryResponse(
    items=items,
    total=total,
    limit=request.limit,
    offset=request.offset,
  )


def query_subgraph_by_source(source_id: str, request: SourceSubgraphQueryRequest) -> GraphSubgraphResponse:
  return get_subgraph_by_source_id(source_id=source_id, limit=request.limit, offset=request.offset)


def query_subgraph_by_sources(request: SourcesSubgraphRequest) -> GraphSubgraphResponse:
  return get_subgraph_by_source_ids(source_ids=request.source_ids, limit=request.limit, offset=request.offset)


def query_subgraph_by_entity(entity_id_or_name: str, request: EntitySubgraphQueryRequest) -> GraphSubgraphResponse:
  return get_subgraph_by_entity(entity_id_or_name=entity_id_or_name, limit=request.limit, offset=request.offset)


def query_subgraph_by_relationship_type(
  request: RelationshipTypeSubgraphQueryRequest,
) -> GraphSubgraphResponse:
  return get_subgraph_by_relationship_type(
    relationship_type=request.relationship_type,
    limit=request.limit,
    offset=request.offset,
  )


def query_subgraph_by_entity_types(request: EntityTypesSubgraphRequest) -> GraphSubgraphResponse:
  return get_subgraph_by_entity_types(
    entity_types=request.entity_types,
    limit=request.limit,
    offset=request.offset,
  )
