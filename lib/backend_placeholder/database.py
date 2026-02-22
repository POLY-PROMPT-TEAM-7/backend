from StudyOntology.lib import Assignment
from StudyOntology.lib import Concept
from StudyOntology.lib import KnowledgeGraph
from StudyOntology.lib import Method
from StudyOntology.lib import Person
from StudyOntology.lib import RelationshipType
from StudyOntology.lib import Theory
from datetime import UTC
from datetime import datetime
from pathlib import Path
import duckdb
from typing import Any
import json
from backend_placeholder.models import EntityRecord
from backend_placeholder.models import GraphSubgraphResponse
from backend_placeholder.models import RelationshipRecord
from backend_placeholder.models import SourceRecord

DB_PATH: Path = Path("/tmp/knowledge.duckdb")


def initialize_db(db_path: Path = DB_PATH) -> None:
  con = duckdb.connect(db_path)
  try:
    con.execute("BEGIN TRANSACTION")
    con.execute(
      """
      CREATE TABLE IF NOT EXISTS ENTITY_TYPES(
        ENTITY_TYPE_ID VARCHAR PRIMARY KEY,
        ENTITY_TYPE_NAME VARCHAR
      )
      """
    )
    con.execute(
      """
      CREATE TABLE IF NOT EXISTS ENTITIES(
        ENTITY_ID VARCHAR PRIMARY KEY,
        ENTITY_NAME VARCHAR,
        NDJSON VARCHAR,
        ENTITY_TYPE_ID VARCHAR
      )
      """
    )
    con.execute(
      """
      CREATE TABLE IF NOT EXISTS SOURCES(
        SOURCE_ID VARCHAR PRIMARY KEY,
        SOURCE_NAME VARCHAR,
        NDJSON VARCHAR
      )
      """
    )
    con.execute(
      """
      CREATE TABLE IF NOT EXISTS RELATIONSHIP_TYPES(
        RELATIONSHIP_TYPE_ID VARCHAR PRIMARY KEY,
        RELATIONSHIP_TYPE_NAME VARCHAR
      )
      """
    )
    con.execute(
      """
      CREATE TABLE IF NOT EXISTS RELATIONSHIPS(
        SUBJECT_ENTITY_ID VARCHAR,
        OBJECT_ENTITY_ID VARCHAR,
        RELATIONSHIP_TYPE_ID VARCHAR,
        NDJSON VARCHAR,
        CONFIDENCE FLOAT,
        PRIMARY KEY(SUBJECT_ENTITY_ID, OBJECT_ENTITY_ID, RELATIONSHIP_TYPE_ID)
      )
      """
    )
    con.execute(
      """
      CREATE TABLE IF NOT EXISTS PROCESSED_ARTIFACTS(
        ARTIFACT_PATH VARCHAR PRIMARY KEY,
        ARTIFACT_SHA256 VARCHAR,
        SOURCE_ID VARCHAR,
        SOURCE_NAME VARCHAR,
        PROCESSED_AT VARCHAR
      )
      """
    )

    con.execute("CREATE INDEX IF NOT EXISTS idx_entity_type_name ON ENTITY_TYPES(ENTITY_TYPE_NAME)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_entity_name ON ENTITIES(ENTITY_NAME)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_entity_type_id ON ENTITIES(ENTITY_TYPE_ID)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_source_name ON SOURCES(SOURCE_NAME)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_rel_type_name ON RELATIONSHIP_TYPES(RELATIONSHIP_TYPE_NAME)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_rel_type_id ON RELATIONSHIPS(RELATIONSHIP_TYPE_ID)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_rel_confidence ON RELATIONSHIPS(CONFIDENCE)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_processed_sha ON PROCESSED_ARTIFACTS(ARTIFACT_SHA256)")

    for entity_class in [Concept, Theory, Person, Method, Assignment]:
      entity_type_name = entity_class.__name__
      con.execute(
        "INSERT OR IGNORE INTO ENTITY_TYPES (ENTITY_TYPE_ID, ENTITY_TYPE_NAME) VALUES (?, ?)",
        [entity_type_name, entity_type_name],
      )

    for rel_type in RelationshipType:
      rel_type_value = rel_type.value if hasattr(rel_type, "value") else str(rel_type)
      con.execute(
        "INSERT OR IGNORE INTO RELATIONSHIP_TYPES (RELATIONSHIP_TYPE_ID, RELATIONSHIP_TYPE_NAME) VALUES (?, ?)",
        [rel_type_value, rel_type_value],
      )

    con.execute("COMMIT")
  except Exception:
    try:
      con.execute("ROLLBACK")
    except Exception:
      pass
    raise
  finally:
    con.close()


def add_data_to_db(kg: KnowledgeGraph, db_path: Path = DB_PATH) -> None:
  con = duckdb.connect(db_path)
  try:
    con.execute("BEGIN TRANSACTION")
    entity_fields: list[tuple[str, str]] = [
      ("concepts", "Concept"),
      ("theories", "Theory"),
      ("persons", "Person"),
      ("methods", "Method"),
      ("assignments", "Assignment"),
    ]
    for field_name, class_name in entity_fields:
      for entity in getattr(kg, field_name, None) or []:
        ndjson = entity.model_dump_json()
        json.loads(ndjson)
        con.execute(
          "INSERT OR REPLACE INTO ENTITIES (ENTITY_ID, ENTITY_NAME, NDJSON, ENTITY_TYPE_ID) VALUES (?, ?, ?, ?)",
          [entity.id, entity.name, ndjson, class_name],
        )

    for source in getattr(kg, "source_documents", None) or []:
      ndjson = source.model_dump_json()
      json.loads(ndjson)
      con.execute(
        "INSERT OR REPLACE INTO SOURCES (SOURCE_ID, SOURCE_NAME, NDJSON) VALUES (?, ?, ?)",
        [source.id, source.name, ndjson],
      )

    for rel in getattr(kg, "relationships", None) or []:
      ndjson = rel.model_dump_json()
      json.loads(ndjson)
      predicate_id = rel.predicate
      if not isinstance(predicate_id, str):
        predicate_id = predicate_id.value if hasattr(predicate_id, "value") else str(predicate_id)
      con.execute(
        "INSERT OR REPLACE INTO RELATIONSHIPS (SUBJECT_ENTITY_ID, OBJECT_ENTITY_ID, RELATIONSHIP_TYPE_ID, NDJSON, CONFIDENCE) VALUES (?, ?, ?, ?, ?)",
        [
          rel.subject,
          rel.object,
          predicate_id,
          ndjson,
          float(rel.confidence) if rel.confidence is not None else None,
        ],
      )
    con.execute("COMMIT")
  except Exception:
    try:
      con.execute("ROLLBACK")
    except Exception:
      pass
    raise
  finally:
    con.close()


def populate_db(kg: KnowledgeGraph, db_path: Path = DB_PATH) -> None:
  initialize_db(db_path)
  add_data_to_db(kg, db_path)


def count_entities(db_path: Path = DB_PATH) -> int:
  con = duckdb.connect(db_path)
  try:
    row = con.execute("SELECT COUNT(*) FROM ENTITIES").fetchone()
    return int(row[0]) if row else 0
  finally:
    con.close()


def count_relationships(db_path: Path = DB_PATH) -> int:
  con = duckdb.connect(db_path)
  try:
    row = con.execute("SELECT COUNT(*) FROM RELATIONSHIPS").fetchone()
    return int(row[0]) if row else 0
  finally:
    con.close()


def get_processed_artifact(artifact_path: str, artifact_sha256: str, db_path: Path = DB_PATH) -> dict[str, Any] | None:
  con = duckdb.connect(db_path)
  try:
    row = con.execute(
      "SELECT ARTIFACT_PATH, ARTIFACT_SHA256, SOURCE_ID, SOURCE_NAME, PROCESSED_AT FROM PROCESSED_ARTIFACTS WHERE ARTIFACT_PATH = ? AND ARTIFACT_SHA256 = ?",
      [artifact_path, artifact_sha256],
    ).fetchone()
    if row is None:
      return None
    return {
      "artifact_path": row[0],
      "artifact_sha256": row[1],
      "source_id": row[2],
      "source_name": row[3],
      "processed_at": row[4],
    }
  finally:
    con.close()


def mark_artifact_processed(artifact_path: str, artifact_sha256: str, source_id: str, source_name: str, db_path: Path = DB_PATH) -> None:
  con = duckdb.connect(db_path)
  try:
    con.execute(
      "INSERT OR REPLACE INTO PROCESSED_ARTIFACTS (ARTIFACT_PATH, ARTIFACT_SHA256, SOURCE_ID, SOURCE_NAME, PROCESSED_AT) VALUES (?, ?, ?, ?, ?)",
      [artifact_path, artifact_sha256, source_id, source_name, datetime.now(tz=UTC).isoformat()],
    )
  finally:
    con.close()


def _loads_json(value: str) -> dict[str, Any]:
  try:
    loaded = json.loads(value)
    if isinstance(loaded, dict):
      return loaded
    return {}
  except Exception:
    return {}


def _collect_source_ids(value: Any, bucket: set[str]) -> None:
  if value is None:
    return
  if isinstance(value, str):
    if value:
      bucket.add(value)
    return
  if isinstance(value, list):
    for item in value:
      _collect_source_ids(item, bucket)
    return
  if isinstance(value, dict):
    for key in ["source_id", "source_document_id"]:
      raw = value.get(key)
      if isinstance(raw, str) and raw:
        bucket.add(raw)
    for key in ["source_ids", "source_document_ids"]:
      raw_list = value.get(key)
      if isinstance(raw_list, list):
        for item in raw_list:
          if isinstance(item, str) and item:
            bucket.add(item)
    if "sources" in value:
      _collect_source_ids(value.get("sources"), bucket)
    if "provenance" in value:
      _collect_source_ids(value.get("provenance"), bucket)


def _source_ids_from_payload(payload: dict[str, Any]) -> set[str]:
  bucket: set[str] = set()
  _collect_source_ids(payload, bucket)
  return bucket


def _relationship_record_from_row(row: tuple[Any, ...]) -> RelationshipRecord:
  payload = _loads_json(str(row[3]))
  return RelationshipRecord(
    subject_entity_id=str(row[0]),
    object_entity_id=str(row[1]),
    relationship_type=str(row[2]),
    confidence=float(row[4]) if row[4] is not None else None,
    data=payload,
  )


def _entity_record_from_row(row: tuple[Any, ...]) -> EntityRecord:
  payload = _loads_json(str(row[2]))
  return EntityRecord(
    entity_id=str(row[0]),
    entity_name=str(row[1]),
    entity_type=str(row[3]),
    data=payload,
  )


def _source_record_from_row(row: tuple[Any, ...]) -> SourceRecord:
  payload = _loads_json(str(row[2]))
  return SourceRecord(
    source_id=str(row[0]),
    source_name=str(row[1]),
    data=payload,
  )


def _fetch_entities_by_ids(entity_ids: set[str], db_path: Path = DB_PATH) -> list[EntityRecord]:
  if not entity_ids:
    return []
  con = duckdb.connect(db_path)
  try:
    placeholders = ", ".join(["?"] * len(entity_ids))
    rows = con.execute(
      f"SELECT ENTITY_ID, ENTITY_NAME, NDJSON, ENTITY_TYPE_ID FROM ENTITIES WHERE ENTITY_ID IN ({placeholders})",
      list(entity_ids),
    ).fetchall()
    return [_entity_record_from_row(row) for row in rows]
  finally:
    con.close()


def _fetch_sources_by_ids(source_ids: set[str], db_path: Path = DB_PATH) -> list[SourceRecord]:
  if not source_ids:
    return []
  con = duckdb.connect(db_path)
  try:
    placeholders = ", ".join(["?"] * len(source_ids))
    rows = con.execute(
      f"SELECT SOURCE_ID, SOURCE_NAME, NDJSON FROM SOURCES WHERE SOURCE_ID IN ({placeholders})",
      list(source_ids),
    ).fetchall()
    return [_source_record_from_row(row) for row in rows]
  finally:
    con.close()


def list_relationships_by_confidence(
  limit: int,
  offset: int,
  min_confidence: float | None = None,
  max_confidence: float | None = None,
  db_path: Path = DB_PATH,
) -> tuple[list[RelationshipRecord], int]:
  con = duckdb.connect(db_path)
  try:
    conditions: list[str] = []
    params: list[Any] = []
    if min_confidence is not None:
      conditions.append("CONFIDENCE >= ?")
      params.append(min_confidence)
    if max_confidence is not None:
      conditions.append("CONFIDENCE <= ?")
      params.append(max_confidence)
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    total_row = con.execute(f"SELECT COUNT(*) FROM RELATIONSHIPS {where_clause}", params).fetchone()
    total = int(total_row[0]) if total_row else 0
    rows = con.execute(
      f"SELECT SUBJECT_ENTITY_ID, OBJECT_ENTITY_ID, RELATIONSHIP_TYPE_ID, NDJSON, CONFIDENCE FROM RELATIONSHIPS {where_clause} ORDER BY CONFIDENCE DESC NULLS LAST, SUBJECT_ENTITY_ID, OBJECT_ENTITY_ID LIMIT ? OFFSET ?",
      [*params, limit, offset],
    ).fetchall()
    return ([_relationship_record_from_row(row) for row in rows], total)
  finally:
    con.close()


def _graph_response_from_relationships(
  relationships: list[RelationshipRecord],
  total_relationships: int,
  limit: int,
  offset: int,
  forced_source_ids: set[str] | None = None,
  forced_entity_ids: set[str] | None = None,
  db_path: Path = DB_PATH,
) -> GraphSubgraphResponse:
  entity_ids: set[str] = set()
  source_ids: set[str] = set(forced_source_ids or set())
  for rel in relationships:
    entity_ids.add(rel.subject_entity_id)
    entity_ids.add(rel.object_entity_id)
    source_ids.update(_source_ids_from_payload(rel.data))
  if forced_entity_ids:
    entity_ids.update(forced_entity_ids)
  entities = _fetch_entities_by_ids(entity_ids, db_path=db_path)
  for entity in entities:
    source_ids.update(_source_ids_from_payload(entity.data))
  sources = _fetch_sources_by_ids(source_ids, db_path=db_path)
  return GraphSubgraphResponse(
    entities=entities,
    relationships=relationships,
    sources=sources,
    total_entities=len(entities),
    total_relationships=total_relationships,
    total_sources=len(sources),
    limit=limit,
    offset=offset,
  )


def get_subgraph_by_source_ids(source_ids: list[str], limit: int, offset: int, db_path: Path = DB_PATH) -> GraphSubgraphResponse:
  source_set = {x for x in source_ids if x}
  if not source_set:
    return GraphSubgraphResponse(
      entities=[],
      relationships=[],
      sources=[],
      total_entities=0,
      total_relationships=0,
      total_sources=0,
      limit=limit,
      offset=offset,
    )

  con = duckdb.connect(db_path)
  try:
    rows = con.execute(
      "SELECT SUBJECT_ENTITY_ID, OBJECT_ENTITY_ID, RELATIONSHIP_TYPE_ID, NDJSON, CONFIDENCE FROM RELATIONSHIPS ORDER BY CONFIDENCE DESC NULLS LAST, SUBJECT_ENTITY_ID, OBJECT_ENTITY_ID"
    ).fetchall()
  finally:
    con.close()

  filtered: list[RelationshipRecord] = []
  for row in rows:
    rel = _relationship_record_from_row(row)
    if _source_ids_from_payload(rel.data) & source_set:
      filtered.append(rel)

  total = len(filtered)
  page = filtered[offset: offset + limit]
  return _graph_response_from_relationships(
    relationships=page,
    total_relationships=total,
    limit=limit,
    offset=offset,
    forced_source_ids=source_set,
    db_path=db_path,
  )


def get_subgraph_by_source_id(source_id: str, limit: int, offset: int, db_path: Path = DB_PATH) -> GraphSubgraphResponse:
  return get_subgraph_by_source_ids(source_ids=[source_id], limit=limit, offset=offset, db_path=db_path)


def get_subgraph_by_entity(entity_id_or_name: str, limit: int, offset: int, db_path: Path = DB_PATH) -> GraphSubgraphResponse:
  con = duckdb.connect(db_path)
  try:
    row = con.execute(
      "SELECT ENTITY_ID FROM ENTITIES WHERE ENTITY_ID = ?",
      [entity_id_or_name],
    ).fetchone()
    if row is None:
      row = con.execute(
        "SELECT ENTITY_ID FROM ENTITIES WHERE LOWER(ENTITY_NAME) = LOWER(?) ORDER BY ENTITY_ID LIMIT 1",
        [entity_id_or_name],
      ).fetchone()
    if row is None:
      return GraphSubgraphResponse(
        entities=[],
        relationships=[],
        sources=[],
        total_entities=0,
        total_relationships=0,
        total_sources=0,
        limit=limit,
        offset=offset,
      )

    entity_id = str(row[0])
    rel_rows = con.execute(
      "SELECT SUBJECT_ENTITY_ID, OBJECT_ENTITY_ID, RELATIONSHIP_TYPE_ID, NDJSON, CONFIDENCE FROM RELATIONSHIPS WHERE SUBJECT_ENTITY_ID = ? OR OBJECT_ENTITY_ID = ? ORDER BY CONFIDENCE DESC NULLS LAST, SUBJECT_ENTITY_ID, OBJECT_ENTITY_ID",
      [entity_id, entity_id],
    ).fetchall()
  finally:
    con.close()

  relationships = [_relationship_record_from_row(row) for row in rel_rows]
  total = len(relationships)
  page = relationships[offset: offset + limit]
  return _graph_response_from_relationships(
    relationships=page,
    total_relationships=total,
    limit=limit,
    offset=offset,
    forced_entity_ids={entity_id},
    db_path=db_path,
  )


def get_subgraph_by_relationship_type(
  relationship_type: str,
  limit: int,
  offset: int,
  db_path: Path = DB_PATH,
) -> GraphSubgraphResponse:
  con = duckdb.connect(db_path)
  try:
    rows = con.execute(
      "SELECT SUBJECT_ENTITY_ID, OBJECT_ENTITY_ID, RELATIONSHIP_TYPE_ID, NDJSON, CONFIDENCE FROM RELATIONSHIPS WHERE RELATIONSHIP_TYPE_ID = ? ORDER BY CONFIDENCE DESC NULLS LAST, SUBJECT_ENTITY_ID, OBJECT_ENTITY_ID",
      [relationship_type],
    ).fetchall()
  finally:
    con.close()

  relationships = [_relationship_record_from_row(row) for row in rows]
  total = len(relationships)
  page = relationships[offset: offset + limit]
  return _graph_response_from_relationships(
    relationships=page,
    total_relationships=total,
    limit=limit,
    offset=offset,
    db_path=db_path,
  )


def get_subgraph_by_entity_types(
  entity_types: list[str],
  limit: int,
  offset: int,
  db_path: Path = DB_PATH,
) -> GraphSubgraphResponse:
  if not entity_types:
    return GraphSubgraphResponse(
      entities=[],
      relationships=[],
      sources=[],
      total_entities=0,
      total_relationships=0,
      total_sources=0,
      limit=limit,
      offset=offset,
    )
  con = duckdb.connect(db_path)
  try:
    placeholders = ", ".join(["?"] * len(entity_types))
    entity_rows = con.execute(
      f"SELECT ENTITY_ID FROM ENTITIES WHERE ENTITY_TYPE_ID IN ({placeholders})",
      entity_types,
    ).fetchall()
    entity_ids = {str(row[0]) for row in entity_rows}
    if not entity_ids:
      return GraphSubgraphResponse(
        entities=[],
        relationships=[],
        sources=[],
        total_entities=0,
        total_relationships=0,
        total_sources=0,
        limit=limit,
        offset=offset,
      )

    rel_placeholders = ", ".join(["?"] * len(entity_ids))
    rel_rows = con.execute(
      f"SELECT SUBJECT_ENTITY_ID, OBJECT_ENTITY_ID, RELATIONSHIP_TYPE_ID, NDJSON, CONFIDENCE FROM RELATIONSHIPS WHERE SUBJECT_ENTITY_ID IN ({rel_placeholders}) AND OBJECT_ENTITY_ID IN ({rel_placeholders}) ORDER BY CONFIDENCE DESC NULLS LAST, SUBJECT_ENTITY_ID, OBJECT_ENTITY_ID",
      [*entity_ids, *entity_ids],
    ).fetchall()
  finally:
    con.close()

  relationships = [_relationship_record_from_row(row) for row in rel_rows]
  total = len(relationships)
  page = relationships[offset: offset + limit]
  return _graph_response_from_relationships(
    relationships=page,
    total_relationships=total,
    limit=limit,
    offset=offset,
    forced_entity_ids=entity_ids,
    db_path=db_path,
  )
