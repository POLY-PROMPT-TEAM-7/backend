import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from pydantic import BaseModel, Field
from typing import Annotated, Literal, List, TypedDict
import operator

from StudyOntology.lib import KnowledgeRelationship, KnowledgeEntity, KnowledgeGraph, SourceDocument

# Import teammate's state (keeping their exact spelling)
from .state import KnowledgeExtractiobhState

load_dotenv()

# =============================================================================
# LLM SETUP
# =============================================================================

llm = ChatOpenAI(
    model="gpt-4o",
    api_key=os.environ["OPENAI_API_KEY"]
)

# =============================================================================
# STRUCTURED OUTPUT SCHEMAS (what the LLM returns)
# =============================================================================

class ExtractedEntities(BaseModel):
    entities: List[KnowledgeEntity]
    relationships: List[KnowledgeRelationship]

class EvaluationResult(BaseModel):
    quality: Literal["good", "needs_improvement"]
    feedback: str = Field(description="What is missing or incorrect")

class DocumentTypeResult(BaseModel):
    document_type: Literal["lecture_slides", "academic_paper", "textbook"]

# Augmented LLMs
extraction_llm = llm.with_structured_output(ExtractedEntities)
evaluation_llm = llm.with_structured_output(EvaluationResult)
router_llm = llm.with_structured_output(DocumentTypeResult)

# =============================================================================
# PATTERN 3: ROUTING
# Detects document type so downstream nodes use specialized prompts
# =============================================================================

def routing_node(state: KnowledgeExtractiobhState):
    """Detect what kind of document this is"""
    result = router_llm.invoke([
        SystemMessage(content="Classify this document as: lecture_slides, academic_paper, or textbook."),
        HumanMessage(content=state["textracted_text"][:500])
    ])
    return {
        "document_type": result.document_type,
        "processing_log": state["processing_log"] + [f"Detected document type: {result.document_type}"]
    }

# =============================================================================
# PATTERN 1: CHAINING
# preprocess → chunk → [parallel extract] → validate → build graph
# Each step feeds into the next
# =============================================================================

def preprocess_node(state: KnowledgeExtractiobhState):
    """Step 1: Clean the raw extracted text"""
    msg = llm.invoke([
        SystemMessage(content="Clean this academic text. Remove headers, footers, page numbers, and formatting artifacts. Return only clean readable text."),
        HumanMessage(content=state["textracted_text"])
    ])
    return {
        "textracted_text": msg.content,
        "processing_log": state["processing_log"] + ["Text preprocessed"]
    }

def chunk_node(state: KnowledgeExtractiobhState):
    """Step 2: Split cleaned text into ~500 word chunks"""
    words = state["textracted_text"].split()
    chunk_size = 500
    chunks = [
        " ".join(words[i:i + chunk_size])
        for i in range(0, len(words), chunk_size)
    ]
    return {
        "chunks": chunks,
        "processing_log": state["processing_log"] + [f"Split into {len(chunks)} chunks"]
    }

def build_graph_node(state: KnowledgeExtractiobhState):
    """Final step: Build KnowledgeGraph from all extracted entities"""
    kg = KnowledgeGraph(
        entities=state["raw_entities"],
        relationships=state["raw_relationships"]
    )
    stats = {
        "entity_count": len(state["raw_entities"]),
        "relationship_count": len(state["raw_relationships"]),
        "validation_errors": len(state["validation_errors"])
    }
    return {
        "knowledge_graph": kg,
        "graph_stats": stats,
        "processing_log": state["processing_log"] + [f"Graph built: {stats}"]
    }

# =============================================================================
# PATTERN 2: PARALLELIZATION
# Each chunk gets its own worker, all run at the same time
# Results are merged back into the main state via Annotated[list, operator.add]
# =============================================================================

class ChunkWorkerState(TypedDict):
    chunk: str
    document_type: str
    raw_entities: Annotated[list, operator.add]
    raw_relationships: Annotated[list, operator.add]
    validation_errors: Annotated[list, operator.add]

def parallel_extract_node(state: ChunkWorkerState):
    """Worker: extract from a single chunk. Runs in parallel for all chunks."""
    prompts = {
        "lecture_slides": "Extract key concepts and their definitions from these lecture slides.",
        "academic_paper": "Extract theories, methods, and findings from this academic paper.",
        "textbook": "Extract concepts and prerequisite relationships from this textbook section."
    }
    prompt = prompts.get(state["document_type"], "Extract academic entities and relationships.")

    result = extraction_llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=state["chunk"])
    ])
    return {
        "raw_entities": result.entities,
        "raw_relationships": result.relationships,
        "validation_errors": []
    }

def assign_chunk_workers(state: KnowledgeExtractiobhState):
    """Fan out: send each chunk to its own parallel worker"""
    return [
        Send("parallel_extract", {
            "chunk": chunk,
            "document_type": state["document_type"],
            "raw_entities": [],
            "raw_relationships": [],
            "validation_errors": []
        })
        for chunk in state["chunks"]
    ]

# =============================================================================
# PATTERN 4: EVALUATOR-OPTIMIZER
# Validate extraction quality, retry with feedback if not good enough
# Capped at 3 retries using retry_count from state
# =============================================================================

def validate_node(state: KnowledgeExtractiobhState):
    """Evaluate whether the extraction is good enough"""
    result = evaluation_llm.invoke([
        SystemMessage(content="""Evaluate this knowledge graph extraction.
        Mark 'good' if main concepts and relationships are captured.
        Mark 'needs_improvement' if key concepts are missing or relationships are wrong."""),
        HumanMessage(content=f"""
            Text (first 500 chars): {state['textracted_text'][:500]}
            Entities found: {len(state['raw_entities'])}
            Relationships found: {len(state['raw_relationships'])}
            Entity names: {[e.name for e in state['raw_entities'][:10]]}
        """)
    ])

    errors = state["validation_errors"]
    if result.quality == "needs_improvement":
        errors = errors + [result.feedback]

    return {
        "validation_errors": errors,
        "retry_count": state["retry_count"] + 1,
        "processing_log": state["processing_log"] + [f"Validation: {result.quality}"]
    }

def should_retry(state: KnowledgeExtractiobhState):
    """Retry if quality is bad, but cap at 3 attempts"""
    if state["validation_errors"] and state["retry_count"] < 3:
        return "retry"
    return "done"

def retry_extract_node(state: KnowledgeExtractiobhState):
    """Re-extract the full document using validation feedback"""
    feedback = state["validation_errors"][-1] if state["validation_errors"] else ""
    result = extraction_llm.invoke([
        SystemMessage(content=f"Re-extract entities and relationships. Previous attempt feedback: {feedback}"),
        HumanMessage(content=state["textracted_text"])
    ])
    return {
        "raw_entities": result.entities,
        "raw_relationships": result.relationships,
        "processing_log": state["processing_log"] + [f"Retry attempt {state['retry_count']}"]
    }

# =============================================================================
# FULL PIPELINE — all 4 patterns wired together
#
#  START
#    → routing          (Pattern 3: detect doc type)
#    → preprocess       (Pattern 1: clean text)
#    → chunk            (Pattern 1: split into chunks)
#    → parallel_extract (Pattern 2: all chunks at once)
#    → validate         (Pattern 4: check quality)
#    → retry if needed  (Pattern 4: retry with feedback)
#    → build_graph
#  END
# =============================================================================

def build_pipeline():
    graph = StateGraph(KnowledgeExtractiobhState)

    # Register all nodes
    graph.add_node("routing", routing_node)
    graph.add_node("preprocess", preprocess_node)
    graph.add_node("chunk", chunk_node)
    graph.add_node("parallel_extract", parallel_extract_node)
    graph.add_node("validate", validate_node)
    graph.add_node("retry_extract", retry_extract_node)
    graph.add_node("build_graph", build_graph_node)

    # Pattern 1 chain: start → routing → preprocess → chunk
    graph.add_edge(START, "routing")
    graph.add_edge("routing", "preprocess")
    graph.add_edge("preprocess", "chunk")

    # Pattern 2 parallel: chunk fans out to workers, workers feed into validate
    graph.add_conditional_edges("chunk", assign_chunk_workers, ["parallel_extract"])
    graph.add_edge("parallel_extract", "validate")

    # Pattern 4 evaluator: validate → retry or finish
    graph.add_conditional_edges("validate", should_retry, {
        "retry": "retry_extract",
        "done": "build_graph"
    })
    graph.add_edge("retry_extract", "validate")

    # Done
    graph.add_edge("build_graph", END)

    return graph.compile()

# Compile once at import time
pipeline = build_pipeline()

# =============================================================================
# PUBLIC API — call this from api.py
# =============================================================================

def process_document(
    filename: str,
    extracted_text: str,
    source_document: SourceDocument = None
) -> KnowledgeExtractiobhState:
    """
    Main entry point. Call this from api.py when a document is uploaded.
    Returns the full final state including knowledge_graph and graph_stats.
    """
    initial_state: KnowledgeExtractiobhState = {
        "filename": filename,
        "document_type": "",
        "textracted_text": extracted_text,
        "source_document": source_document,
        "chunks": [],
        "raw_entities": [],
        "raw_relationships": [],
        "validation_errors": [],
        "retry_count": 0,
        "knowledge_graph": None,
        "graph_stats": {},
        "processing_log": [f"Started processing: {filename}"]
    }

    return pipeline.invoke(initial_state)