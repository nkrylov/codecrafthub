"""REST API endpoints for CodeCraftHub courses."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from . import storage
from .models import validate_course

bp = Blueprint("courses", __name__)


def _error(message: str, status: int):
    """Uniform JSON error envelope."""
    return jsonify({"error": message}), status


# GET /health -> simple liveness probe used by the test script.
@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


# GET /courses -> list every stored course.
@bp.get("/courses")
def list_courses():
    return jsonify(storage.list_courses())


# GET /courses/<id> -> fetch a single course by its integer ID.
@bp.get("/courses/<int:course_id>")
def get_course(course_id: int):
    course = storage.get_course(course_id)
    if course is None:
        return _error(f"Course {course_id} not found.", 404)
    return jsonify(course)


# POST /courses -> create a new course, auto-assigning the next integer ID.
@bp.post("/courses")
def create_course():
    payload = request.get_json(silent=True)
    clean, err = validate_course(payload, partial=False)
    if err:
        return _error(err, 400)
    course = storage.create_course(clean)
    return jsonify(course), 201


# PUT /courses/<id> -> full replacement of a course (all required fields).
@bp.put("/courses/<int:course_id>")
def replace_course(course_id: int):
    payload = request.get_json(silent=True)
    clean, err = validate_course(payload, partial=False)
    if err:
        return _error(err, 400)
    updated = storage.update_course(course_id, clean, partial=False)
    if updated is None:
        return _error(f"Course {course_id} not found.", 404)
    return jsonify(updated)


# PATCH /courses/<id> -> partial update (e.g. change status only).
@bp.patch("/courses/<int:course_id>")
def patch_course(course_id: int):
    payload = request.get_json(silent=True)
    clean, err = validate_course(payload, partial=True)
    if err:
        return _error(err, 400)
    if not clean:
        return _error("No valid fields provided to update.", 400)
    updated = storage.update_course(course_id, clean, partial=True)
    if updated is None:
        return _error(f"Course {course_id} not found.", 404)
    return jsonify(updated)


# DELETE /courses/<id> -> remove a course; returns 204 on success.
@bp.delete("/courses/<int:course_id>")
def delete_course(course_id: int):
    if not storage.delete_course(course_id):
        return _error(f"Course {course_id} not found.", 404)
    return "", 204

