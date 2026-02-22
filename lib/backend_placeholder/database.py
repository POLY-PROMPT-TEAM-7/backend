import duckdb
import importlib
import json


class KnowledgeGraph:
  pass

"""
# SCHEMA

## ENTITY_TYPES
- ENTITY_TYPE_ID VARCHAR PRIMARY KEY
- ENTITY_TYPE_NAME VARCHAR
- INDEX ON (ENTITY_TYPE_NAME)

## ENTITIES
- ENTITY_ID VARCHAR PRIMARY KEY
- ENTITY_NAME VARCHAR
- NDJSON VARCHAR
- ENTITY_TYPE_ID VARCHAR REFERENCES ENTITY_TYPES(ENTITY_TYPE_ID)
- INDEX ON (ENTITY_NAME)

## SOURCES
- SOURCE_ID VARCHAR PRIMARY KEY
- SOURCE_NAME VARCHAR
- NDJSON VARCHAR
- INDEX ON (SOURCE_NAME)

## RELATIONSHIP_TYPES
- RELATIONSHIP_TYPE_ID VARCHAR PRIMARY KEY
- RELATIONSHIP_TYPE_NAME VARCHAR
- INDEX ON (RELATIONSHIP_TYPE_NAME)

## RELATIONSHIPS
- SUBJECT_ENTITY_ID VARCHAR REFERENCES ENTITIES(ENTITY_ID)
- OBJECT_ENTITY_ID VARCHAR REFERENCES ENTITIES(ENTITY_ID)
- RELATIONSHIP_TYPE_ID VARCHAR REFERENCES RELATIONSHIP_TYPES(RELATIONSHIP_TYPE_ID)
- NDJSON VARCHAR
- CONFIDENCE FLOAT
- INDEX ON (CONFIDENCE)
"""

DB_PATH: str = "/tmp/knowledge.db"

ENTITY_TYPE_MAP: dict[str, str] = {
  "Concept": "CONCEPT",
  "Theory": "THEORY",
  "Person": "PERSON",
  "Method": "METHOD",
  "Assignment": "ASSIGNMENT",
}


def populate_db(kg: KnowledgeGraph, db_path: str = DB_PATH) -> None:
  study_lib = importlib.import_module("StudyOntology.lib")
  RelationshipType = getattr(study_lib, "RelationshipType")

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
      "CREATE INDEX IF NOT EXISTS idx_entity_type_name ON ENTITY_TYPES(ENTITY_TYPE_NAME)"
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_entity_name ON ENTITIES(ENTITY_NAME)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_source_name ON SOURCES(SOURCE_NAME)")
    con.execute(
      "CREATE INDEX IF NOT EXISTS idx_rel_type_name ON RELATIONSHIP_TYPES(RELATIONSHIP_TYPE_NAME)"
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_rel_confidence ON RELATIONSHIPS(CONFIDENCE)")

    for entity_type_name in ENTITY_TYPE_MAP.values():
      con.execute(
        "INSERT OR IGNORE INTO ENTITY_TYPES (ENTITY_TYPE_ID, ENTITY_TYPE_NAME) VALUES (?, ?)",
        [entity_type_name, entity_type_name],
      )

    for rel_type in RelationshipType:
      rel_type_value = rel_type.value
      con.execute(
        "INSERT OR IGNORE INTO RELATIONSHIP_TYPES (RELATIONSHIP_TYPE_ID, RELATIONSHIP_TYPE_NAME) VALUES (?, ?)",
        [rel_type_value, rel_type_value],
      )

    con.execute("DELETE FROM RELATIONSHIPS")
    con.execute("DELETE FROM ENTITIES")
    con.execute("DELETE FROM SOURCES")

    entity_fields: list[tuple[str, str]] = [
      ("concepts", "Concept"),
      ("theories", "Theory"),
      ("persons", "Person"),
      ("methods", "Method"),
      ("assignments", "Assignment"),
    ]
    for field_name, class_name in entity_fields:
      entity_type_id = ENTITY_TYPE_MAP[class_name]
      for entity in getattr(kg, field_name, None) or []:
        ndjson = entity.model_dump_json()
        json.loads(ndjson)
        con.execute(
          "INSERT OR REPLACE INTO ENTITIES (ENTITY_ID, ENTITY_NAME, NDJSON, ENTITY_TYPE_ID) VALUES (?, ?, ?, ?)",
          [entity.id, entity.name, ndjson, entity_type_id],
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

      predicate = rel.predicate
      predicate_id = predicate.value if hasattr(predicate, "value") else str(predicate)

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
  except Exception as exc:
    try:
      con.execute("ROLLBACK")
    except Exception as rollback_exc:
      raise exc from rollback_exc
    raise
  finally:
    con.close()
