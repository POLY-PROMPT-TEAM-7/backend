from StudyOntology.lib import Assignment
import requests
import os

CANVAS_API_KEY: str = os.environ["CANVAS_API_KEY"]
HEADERS: dict[str, str] = {"Authorization": f"Bearer {CANVAS_API_KEY}"}

def get_courses() -> list[dict]:
  response: object = requests.get("https://canvas.calpoly.edu/api/v1/courses", headers=HEADERS)
  response.raise_for_status()
  return response.json()

def get_assignments(course_id: int) -> list[dict]:
  response: object = requests.get(f"https://canvas.calpoly.edu/api/v1/courses/{course_id}/assignments", headers=HEADERS)
  response.raise_for_status()
  return response.json()

def filter_active_courses(courses: list[dict]) -> list[dict]:
  return [c for c in courses if c.get("workflow_state") == "available" and c.get("name")]

def build_assignments(active_courses: list[dict]) -> list[Assignment]:
  assignments: list[Assignment] = []

  for course in active_courses:
    course_id: int = course["id"]
    course_name: str = course["name"]
    raw_assignments: list[dict] = get_assignments(course_id)

    for a in raw_assignments:
      assignments += [Assignment(
        course_id=course_id,
        course_name=course_name,
        name=a.get("name", "Untitled"),
        description=a.get("description"),
        canvas_assignment_id=a.get("id"),
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
  raw_courses: list[dict] = get_courses()
  active_courses: list[dict] = filter_active_courses(raw_courses)
  assignments: list[Assignment] = build_assignments(active_courses)

  return {
    "canvas_courses": active_courses,
    "canvas_assignments": [a.model_dump() for a in assignments],
    "processing_log": state["processing_log"] + [f"Fetched {len(active_courses)} courses and {len(assignments)} assignments from Canvas"]
  }
