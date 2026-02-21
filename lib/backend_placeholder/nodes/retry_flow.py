from backend_placeholder.state import KnowledgeExtractionState
from typing import Literal

MAX_RETRIES: int = 3

def route_after_validate(state: KnowledgeExtractionState) -> Literal["retry", "done"]:
  has_errors: bool = bool(state.get("validation_errors", []))
  retries: int = state.get("retry_count", 0)
  if has_errors and retries < MAX_RETRIES:
    return "retry"
  return "done"
