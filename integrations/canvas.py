import json
import os
import requests
from typing import Optional
from StudyOntology.lib import Assignment

MOCK_MODE: bool = True

# API CALLS

def get_courses(token: Optional[str] = None) -> list[dict]:
  """Fetch all courses — mock or real Canvas API"""
  if MOCK_MODE:
    mock_path: str = os.path.join(os.path.dirname(__file__), "CanvasJsonformat.json")
    with open(mock_path) as f:
      return json.load(f)
  else:
    response = requests.get(
      "https://canvas.calpoly.edu/api/v1/courses",
      headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    return response.json()

def get_assignments(course_id: int, token: Optional[str] = None) -> list[dict]:
  """Fetch all assignments for a given course"""
  if MOCK_MODE:
    return []
  else:
    response = requests.get(
      f"https://canvas.calpoly.edu/api/v1/courses/{course_id}/assignments",
      headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    return response.json()

# HELPERS

def filter_active_courses(courses: list[dict]) -> list[dict]:
  """Keep only courses that are active and have a name"""
  return [
    c for c in courses
    if c.get("workflow_state") == "available" and c.get("name")
  ]

def build_assignments(
  active_courses: list[dict],
  token: Optional[str]
) -> list[Assignment]:
  """Fetch assignments and map to ontology Assignment objects"""
  assignments: list[Assignment] = []

  for course in active_courses:
    course_id: int = course["id"]
    course_name: str = course["name"]
    raw_assignments: list[dict] = get_assignments(course_id, token)

    for a in raw_assignments:
      assignments.append(Assignment(
        id=str(a.get("id")),
        name=a.get("name", "Untitled"),
        description=a.get("description"),
        canvas_assignment_id=a.get("id"),
        due_date=a.get("due_at"),
        points_possible=a.get("points_possible"),
        html_url=a.get("html_url"),
        is_published=a.get("published"),
        submission_types=a.get("submission_types", [])
      ))

  return assignments

# LANGGRAPH NODE

def canvas_node(state: dict) -> dict:
  """
  LangGraph node: fetch Canvas courses and assignments, store in state.
  """
  token: Optional[str] = os.environ.get("CANVAS_API_KEY")

  raw_courses: list[dict] = get_courses(token)
  active_courses: list[dict] = filter_active_courses(raw_courses)
  assignments: list[Assignment] = build_assignments(active_courses, token)

  return {
    "canvas_courses": active_courses,
    "canvas_assignments": [a.model_dump() for a in assignments],
    "processing_log": state["processing_log"] + [
      f"Fetched {len(active_courses)} courses and {len(assignments)} assignments from Canvas"
    ]
  }