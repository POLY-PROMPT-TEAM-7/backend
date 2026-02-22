import pytest
from integrations.canvas import (
  get_courses,
  filter_active_courses,
  build_courses,
  canvas_node
)

def test_get_courses_returns_list():
  courses = get_courses()
  assert isinstance(courses, list)
  assert len(courses) > 0

def test_filter_active_courses_removes_restricted():
  courses = get_courses()
  active = filter_active_courses(courses)
  assert all(c.get("workflow_state") == "available" for c in active)
  assert all(c.get("name") is not None for c in active)

def test_build_courses_has_correct_fields():
  courses = get_courses()
  active = filter_active_courses(courses)
  built = build_courses(active)
  for c in built:
    assert c.name is not None
    assert c.id is not None
    assert c.color.startswith("#")

def test_canvas_node_updates_state():
  result = canvas_node({"processing_log": []})
  assert "canvas_courses" in result
  assert "canvas_assignments" in result
  assert len(result["processing_log"]) == 1