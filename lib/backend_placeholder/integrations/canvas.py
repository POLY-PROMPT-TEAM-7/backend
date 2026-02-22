from StudyOntology.lib import Assignment
import requests
from typing import Any
import os

def get_canvas_api_key() -> str:
  return os.getenv("CANVAS_API_KEY", "")

def get_headers() -> dict[str, str]:
  return {"Authorization": f"Bearer {get_canvas_api_key()}"}

def get_courses() -> list[dict[str, Any]]:
  response: object = requests.get("https://canvas.calpoly.edu/api/v1/courses", headers=get_headers())
  response.raise_for_status()
  return response.json()

def get_assignments(course_id: int) -> list[dict[str, Any]]:
  response: object = requests.get(f"https://canvas.calpoly.edu/api/v1/courses/{course_id}/assignments", headers=get_headers())
  response.raise_for_status()
  return response.json()

def filter_active_courses(courses: list[dict[str, Any]]) -> list[dict[str, Any]]:
  return [c for c in courses if c.get("workflow_state") == "available" and c.get("name")]

def build_assignments(active_courses: list[dict[str, Any]]) -> list[Assignment]:
  assignments: list[Assignment] = []

  for course in active_courses:
    course_id: int = course["id"]
    course_name: str = course["name"]
    raw_assignments: list[dict[str, Any]] = get_assignments(course_id)

    for a in raw_assignments:
      canvas_assignment_id: Any = a.get("id")
      if canvas_assignment_id is None:
        continue

      assignments += [Assignment(
        id=f"assignment:{canvas_assignment_id}",
        course_id=str(course_id),
        course_name=course_name,
        name=a.get("name", "Untitled"),
        description=a.get("description"),
        canvas_assignment_id=canvas_assignment_id,
        due_date=a.get("due_at"),
        points_possible=a.get("points_possible"),
        html_url=a.get("html_url"),
        is_published=a.get("published"),
        submission_types=a.get("submission_types", [])
      )]

  return assignments

def canvas_node(state: dict) -> dict:
  """
  LangGraph node: fetch Canvas courses and assignments, store in state.
  """
  # Graceful degradation: skip if API key missing or request fails
  if not state.get("query_canvas", False):
    print("[canvas_node] skipped query_canvas=False")
    return {
      "canvas_courses": state.get("canvas_courses", []),
      "canvas_assignments": state.get("canvas_assignments", []),
      "processing_log": state.get("processing_log", [])
    }
  if get_canvas_api_key() == "":
    print("[canvas_node] skipped missing CANVAS_API_KEY")
    return {
      "canvas_courses": [],
      "canvas_assignments": [],
      "processing_log": state.get("processing_log", [])
    }

  try:
    raw_courses: list[dict[str, Any]] = get_courses()
    active_courses: list[dict[str, Any]] = filter_active_courses(raw_courses)
    assignments: list[Assignment] = build_assignments(active_courses)
    print(f"[canvas_node] fetched courses={len(active_courses)} assignments={len(assignments)}")

    return {
      "canvas_courses": active_courses,
      "canvas_assignments": assignments,
      "processing_log": state.get("processing_log", [])
    }
  except Exception as e:
    print(f"[canvas_node] failed: {e}")
    return {
      "canvas_courses": [],
      "canvas_assignments": [],
      "processing_log": state.get("processing_log", [])
    }
