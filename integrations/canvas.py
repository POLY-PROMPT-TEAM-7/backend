import json
import os
import requests
from typing import Optional, TypedDict

MOCK_MODE: bool = True

# TYPES

CanvasAssignment = TypedDict('CanvasAssignment', {
  'course_name': str,
  'assignment_name': str,
  'assignment_description': Optional[str],
  'deadline': Optional[str]
})

CanvasCourse = TypedDict('CanvasCourse', {
  'id': int,
  'name': str
})

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
    return []  # swap in mock assignments here when ready
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
) -> list[CanvasAssignment]:
  """Fetch assignments for each course and attach course name, description, deadline"""
  assignments: list[CanvasAssignment] = []

  for course in active_courses:
    course_id: int = course["id"]
    course_name: str = course["name"]
    raw_assignments: list[dict] = get_assignments(course_id, token)

    for a in raw_assignments:
      assignments.append(CanvasAssignment(
        course_name=course_name,
        assignment_name=a.get("name", "Untitled"),
        assignment_description=a.get("description"),
        deadline=a.get("due_at")
      ))

  return assignments

def build_courses(active_courses: list[dict]) -> list[CanvasCourse]:
  """Convert raw course dicts into typed CanvasCourse objects"""
  return [
    CanvasCourse(
      id=c["id"],
      name=c["name"]
    )
    for c in active_courses
  ]

# LANGGRAPH NODE

def canvas_node(state: dict) -> dict:
  """
  LangGraph node: fetch Canvas courses and assignments, store in state.
  Requires state to have: processing_log, canvas_courses, canvas_assignments
  """
  token: Optional[str] = os.environ.get("CANVAS_API_KEY")

  raw_courses: list[dict] = get_courses(token)
  active_courses: list[dict] = filter_active_courses(raw_courses)

  courses: list[CanvasCourse] = build_courses(active_courses)
  assignments: list[CanvasAssignment] = build_assignments(active_courses, token)

  return {
    "canvas_courses": courses,
    "canvas_assignments": assignments,
    "processing_log": state["processing_log"] + [
      f"Fetched {len(courses)} courses and {len(assignments)} assignments from Canvas"
    ]
  }