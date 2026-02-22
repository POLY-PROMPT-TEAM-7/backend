from backend_placeholder.state import KnowledgeExtractionState
from StudyOntology.lib import KnowledgeRelationship
from StudyOntology.lib import ExtractionProvenance
from StudyOntology.lib import RelationshipType
from StudyOntology.lib import KnowledgeEntity
from StudyOntology.lib import SourceDocument
from StudyOntology.lib import Concept
from typing import Optional
from typing import Any
import httpx
import os

BASE_URL: str = "https://api.openalex.org"
API_KEY: str = os.environ["OPENALEX_API_KEY"]

def make_provenance(concept_name: str) -> ExtractionProvenance:
  return ExtractionProvenance(
    source_document=f"openalex:source:{concept_name.lower().replace(' ', '_')}",
    extraction_method="OpenAlex API enrichment",
    raw_text=f"Enriched from OpenAlex knowledge graph for concept: {concept_name}"
  )

TIMEOUT: float = 30.0
HEADERS: dict[str, str] = {"User-Agent": "KGStudyTool/1.0"}

def search_openalex_concept(name: str) -> Optional[dict[str, Any]]:
  try:
    resp: httpx.Response = httpx.get(
      f"{BASE_URL}/concepts",
      params={"search": name, "per-page": 1, "api_key": API_KEY},
      headers=HEADERS,
      timeout=TIMEOUT
    )
    resp.raise_for_status()
    results: list[dict[str, Any]] = resp.json().get("results", [])
    return results[0] if results else None
  except Exception:
    return None

def get_top_papers(
  openalex_concept_id: str,
  limit: int = 3
) -> list[dict[str, Any]]:
  try:
    resp: httpx.Response = httpx.get(
      f"{BASE_URL}/works",
      params={"filter": f"concepts.id:{openalex_concept_id}", "sort": "cited_by_count:desc", "per-page": limit, "api_key": API_KEY},
      headers=HEADERS,
      timeout=TIMEOUT
    )
    resp.raise_for_status()
    return resp.json().get("results", [])
  except Exception:
    return []

def enrich_single_concept(
  entity: Concept
) -> tuple[list[KnowledgeEntity], list[KnowledgeRelationship]]:
  new_entities: list[KnowledgeEntity] = []
  new_relationships: list[KnowledgeRelationship] = []

  oa_concept: Optional[dict[str, Any]] = search_openalex_concept(entity.name)
  if oa_concept is None:
    return new_entities, new_relationships

  oa_id: str = oa_concept["id"]
  provenance: ExtractionProvenance = make_provenance(entity.name)

  ancestor: dict[str, Any]
  for ancestor in (oa_concept.get("ancestors") or []):
    ancestor_name: str = ancestor.get("display_name", "")
    if not ancestor_name:
      continue
    ancestor_id: str = f"openalex:concept:{ancestor['id'].split('/')[-1]}"
    ancestor_node: Concept = Concept(
      id=ancestor_id,
      name=ancestor_name,
      description=f"Broader topic related to {entity.name} (from OpenAlex)",
      sources=[provenance]
    )
    new_entities.append(ancestor_node)
    new_relationships.append(
      KnowledgeRelationship(
        subject=ancestor_id,
        predicate=RelationshipType.PREREQUISITE_OF,
        object=entity.id,
        confidence=0.75,
        provenance=provenance,
        notes=f"OpenAlex ancestor concept of {entity.name}"
      )
    )

  related: dict[str, Any]
  for related in (oa_concept.get("related_concepts") or [])[:5]:
    related_name: str = related.get("display_name", "")
    if not related_name:
      continue
    related_id: str = f"openalex:concept:{related['id'].split('/')[-1]}"
    related_node: Concept = Concept(
      id=related_id,
      name=related_name,
      description=f"Peer concept related to {entity.name} (from OpenAlex)",
      sources=[provenance]
    )
    new_entities.append(related_node)
    new_relationships.append(
      KnowledgeRelationship(
        subject=related_id,
        predicate=RelationshipType.CONTRASTS_WITH,
        object=entity.id,
        confidence=0.65,
        provenance=provenance,
        notes=f"OpenAlex related concept of {entity.name}"
      )
    )

  paper: dict[str, Any]
  for paper in get_top_papers(oa_id):
    title: str = paper.get("display_name") or "Untitled Paper"
    doi: str = paper.get("doi") or paper.get("id", "")
    paper_short_id: str = paper["id"].split("/")[-1]
    cited_by: int = paper.get("cited_by_count", 0)
    paper_doc: SourceDocument = SourceDocument(
      id=f"openalex:paper:{paper_short_id}",
      name=title,
      description=f"Academic paper cited {cited_by} times. Source: OpenAlex.",
      document_type="academic_paper",
      origin="WEB_SCRAPE",
      file_path=doi
    )
    new_entities.append(paper_doc)
    new_relationships.append(
      KnowledgeRelationship(
        subject=f"openalex:paper:{paper_short_id}",
        predicate=RelationshipType.APPLIES_TO,
        object=entity.id,
        confidence=0.9,
        provenance=provenance,
        notes=f"Cited {cited_by} times on OpenAlex"
      )
    )

  return new_entities, new_relationships

def enrich_with_openalex(state: KnowledgeExtractionState) -> dict[str, Any]:
  raw_entities: list[KnowledgeEntity] = state.get("raw_entities", [])
  raw_relationships: list[KnowledgeRelationship] = state.get("raw_relationships", [])

  concepts_to_enrich: list[Concept] = [e for e in raw_entities if isinstance(e, Concept)]

  all_new_entities: list[KnowledgeEntity] = []
  all_new_relationships: list[KnowledgeRelationship] = []

  concept: Concept
  for concept in concepts_to_enrich:
    new_entities: list[KnowledgeEntity]
    new_relationships: list[KnowledgeRelationship]
    new_entities, new_relationships = enrich_single_concept(concept)
    all_new_entities.extend(new_entities)
    all_new_relationships.extend(new_relationships)

  existing_ids: set[str] = {e.id for e in raw_entities}
  deduped_new_entities: list[KnowledgeEntity] = [e for e in all_new_entities if e.id not in existing_ids]

  merged_entities: list[KnowledgeEntity] = raw_entities + deduped_new_entities
  merged_relationships: list[KnowledgeRelationship] = raw_relationships + all_new_relationships

  log_msg: str = f"[enrich_with_openalex] Enriched {len(concepts_to_enrich)} concepts. Added {len(deduped_new_entities)} new entities and {len(all_new_relationships)} new relationships."

  return {
    "raw_entities": merged_entities,
    "raw_relationships": merged_relationships,
    "enriched_entities": deduped_new_entities,
    "enriched_relationships": all_new_relationships,
    "processing_log": state.get("processing_log", []) + [log_msg]
  }