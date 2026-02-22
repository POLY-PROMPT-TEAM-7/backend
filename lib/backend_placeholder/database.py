from StudyOntology.lib import RelationshipType
from StudyOntology.lib import KnowledgeGraph
from StudyOntology.lib import Assignment
from StudyOntology.lib import Concept 
from StudyOntology.lib import Theory
from StudyOntology.lib import Person
from StudyOntology.lib import Method
from pathlib import Path
import duckdb
import json

DB_PATH: Path = Path("/tmp/knowledge.duckdb")

def initialize_db(db_path: Path = DB_PATH) -> None:
  """
  Initialize DuckDB database with schema and metadata.
  
  Args:
    db_path: Path to DuckDB database file (defaults to DB_PATH)
  Note:
    Creates tables, indexes, and populates entity/relationship types.
    Does NOT delete existing data. Safe to run multiple times.
  """
  con = duckdb.connect(db_path)
  try:
    con.execute("BEGIN TRANSACTION")

    # Create entity types table
    con.execute(
      """
      CREATE TABLE IF NOT EXISTS ENTITY_TYPES(
        ENTITY_TYPE_ID VARCHAR PRIMARY KEY,
        ENTITY_TYPE_NAME VARCHAR
      )
      """
    )
    
    # Create entities table
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
    
    # Create sources table
    con.execute(
      """
      CREATE TABLE IF NOT EXISTS SOURCES(
        SOURCE_ID VARCHAR PRIMARY KEY,
        SOURCE_NAME VARCHAR,
        NDJSON VARCHAR
      )
      """
    )
    
    # Create relationship types table
    con.execute(
      """
      CREATE TABLE IF NOT EXISTS RELATIONSHIP_TYPES(
        RELATIONSHIP_TYPE_ID VARCHAR PRIMARY KEY,
        RELATIONSHIP_TYPE_NAME VARCHAR
      )
      """
    )
    
    # Create relationships table
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

    # Create indexes for performance
    con.execute(
      "CREATE INDEX IF NOT EXISTS idx_entity_type_name ON ENTITY_TYPES(ENTITY_TYPE_NAME)"
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_entity_name ON ENTITIES(ENTITY_NAME)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_source_name ON SOURCES(SOURCE_NAME)")
    con.execute(
      "CREATE INDEX IF NOT EXISTS idx_rel_type_name ON RELATIONSHIP_TYPES(RELATIONSHIP_TYPE_NAME)"
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_rel_confidence ON RELATIONSHIPS(CONFIDENCE)")

    # Populate entity types
    entity_classes = [Concept, Theory, Person, Method, Assignment]
    for entity_class in entity_classes:
      entity_type_name = entity_class.__name__
      con.execute(
        "INSERT OR IGNORE INTO ENTITY_TYPES (ENTITY_TYPE_ID, ENTITY_TYPE_NAME) VALUES (?, ?)",
        [entity_type_name, entity_type_name],
      )

    # Populate relationship types
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
  """
  Add knowledge graph data to DuckDB database without deleting existing data.
  
  Args:
    kg: KnowledgeGraph object containing entities, relationships, and sources
    db_path: Path to DuckDB database file (defaults to DB_PATH)
  Note:
    This function uses INSERT OR REPLACE to handle duplicates.
    Existing data is preserved unless explicitly replaced.
  """
  con = duckdb.connect(db_path)
  try:
    con.execute("BEGIN TRANSACTION")

    # Insert entities by type
    entity_fields: list[tuple[str, str]] = [
      ("concepts", "Concept"),
      ("theories", "Theory"),
      ("persons", "Person"),
      ("methods", "Method"),
      ("assignments", "Assignment"),
    ]
    for field_name, class_name in entity_fields:
      entity_type_id = class_name
      for entity in getattr(kg, field_name, None) or []:
        ndjson = entity.model_dump_json()
        # Validate JSON before insertion
        json.loads(ndjson)
        con.execute(
          "INSERT OR REPLACE INTO ENTITIES (ENTITY_ID, ENTITY_NAME, NDJSON, ENTITY_TYPE_ID) VALUES (?, ?, ?, ?)",
          [entity.id, entity.name, ndjson, entity_type_id],
        )

    # Insert source documents
    for source in getattr(kg, "source_documents", None) or []:
      ndjson = source.model_dump_json()
      # Validate JSON before insertion
      json.loads(ndjson)
      con.execute(
        "INSERT OR REPLACE INTO SOURCES (SOURCE_ID, SOURCE_NAME, NDJSON) VALUES (?, ?, ?)",
        [source.id, source.name, ndjson],
      )

    # Insert relationships
    for rel in getattr(kg, "relationships", None) or []:
      ndjson = rel.model_dump_json()
      # Validate JSON before insertion
      json.loads(ndjson)
      
      # Handle both string and enum predicate types
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
  """
  Populate DuckDB database with knowledge graph data.
  
  Args:
    kg: KnowledgeGraph object containing entities, relationships, and sources
    db_path: Path to DuckDB database file (defaults to DB_PATH)
  Note:
    This function uses transaction management to ensure data consistency.
    Calls initialize_db() and add_data_to_db() internally.
    Use initialize_db() separately if you want to set up the schema once,
    then use add_data_to_db() to add multiple knowledge graphs.
  """
  initialize_db(db_path)
  add_data_to_db(kg, db_path)
