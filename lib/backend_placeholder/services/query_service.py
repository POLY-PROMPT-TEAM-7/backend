from backend_placeholder.database import get_subgraph_by_entity
from backend_placeholder.database import get_subgraph_by_entity_types
from backend_placeholder.database import get_subgraph_by_relationship_type
from backend_placeholder.database import get_subgraph_by_source_id
from backend_placeholder.database import get_subgraph_by_source_ids
from backend_placeholder.database import list_relationships_by_confidence
from backend_placeholder.models import EntitySubgraphQueryRequest
from backend_placeholder.models import EntityTypesSubgraphRequest
from backend_placeholder.models import GraphSubgraphResponse
from backend_placeholder.models import RelationshipTypeSubgraphQueryRequest
from backend_placeholder.models import RelationshipsQueryRequest
from backend_placeholder.models import RelationshipsQueryResponse
from backend_placeholder.models import SourceSubgraphQueryRequest
from backend_placeholder.models import SourcesSubgraphRequest

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
