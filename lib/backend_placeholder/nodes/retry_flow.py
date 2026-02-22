from backend_placeholder.state import KnowledgeExtractionState
from typing import Literal

MAX_RETRIES: int = 3

def route_after_validate(state: KnowledgeExtractionState) -> Literal["retry", "fail", "done"]:
  # Fail-fast: skip external APIs when LLM retries exhausted
  has_errors: bool = bool(state.get("validation_errors", []))
  retries: int = state.get("retry_count", 0)
  if has_errors and retries < MAX_RETRIES:
    return "retry"
  if has_errors and retries >= MAX_RETRIES:
    return "fail"
  return "done"
