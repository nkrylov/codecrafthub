"""JSON file storage for courses.

- Uses a threading.Lock for in-process safety.
- Uses os.replace on a temp file for atomic writes (no partial/corrupted JSON).
- Only whitelisted fields are persisted (see app.models.ALLOWED_FIELDS).
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
from typing import List, Optional

from .models import ALLOWED_FIELDS, DEFAULT_STATUS

_LOCK = threading.Lock()

# Default location; can be overridden with the CODECRAFTHUB_DATA_FILE env var.
_DEFAULT_DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "courses.json",
)


def get_data_file() -> str:
    """Return the path of the JSON data file (env-overridable)."""
    return os.environ.get("CODECRAFTHUB_DATA_FILE", _DEFAULT_DATA_FILE)


def _empty_state() -> dict:
    return {"next_id": 1, "courses": []}


def _ensure_file(path: str) -> None:
    """Create the data file with an empty state if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _atomic_write(path, _empty_state())


def _atomic_write(path: str, data: dict) -> None:
    """Write JSON atomically to avoid partial files on crash."""
    directory = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".courses-", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            json.dump(data, tmp, indent=2, ensure_ascii=False)
            tmp.write("\n")
        os.replace(tmp_path, path)
    except Exception:
        # Clean up temp file if something went wrong before replace().
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _load() -> dict:
    path = get_data_file()
    _ensure_file(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Defensive defaults in case someone hand-edits the file.
    data.setdefault("next_id", 1)
    data.setdefault("courses", [])
    return data


def _save(data: dict) -> None:
    _atomic_write(get_data_file(), data)


def _sanitize(course: dict) -> dict:
    """Keep only whitelisted fields so JSON never accumulates unknown keys."""
    return {k: course[k] for k in ALLOWED_FIELDS if k in course}


# ---------- Public CRUD API ----------

def list_courses() -> List[dict]:
    with _LOCK:
        return _load()["courses"]


def get_course(course_id: int) -> Optional[dict]:
    with _LOCK:
        for c in _load()["courses"]:
            if c["id"] == course_id:
                return c
    return None


def create_course(clean_payload: dict) -> dict:
    """Assign the next integer ID and persist. Applies default status."""
    with _LOCK:
        data = _load()
        new_id = int(data["next_id"])
        course = _sanitize(clean_payload)
        course.setdefault("status", DEFAULT_STATUS)
        course = {"id": new_id, **course}
        data["courses"].append(course)
        data["next_id"] = new_id + 1
        _save(data)
        return course


def update_course(
    course_id: int, clean_payload: dict, partial: bool = False
) -> Optional[dict]:
    """Update an existing course. Returns the updated course, or None if missing."""
    with _LOCK:
        data = _load()
        for idx, c in enumerate(data["courses"]):
            if c["id"] == course_id:
                clean = _sanitize(clean_payload)
                if partial:
                    updated = {**c, **clean}
                else:
                    # Full replace: keep id + status default if not provided.
                    updated = {"id": course_id, **clean}
                    updated.setdefault("status", DEFAULT_STATUS)
                data["courses"][idx] = updated
                _save(data)
                return updated
    return None


def delete_course(course_id: int) -> bool:
    with _LOCK:
        data = _load()
        for idx, c in enumerate(data["courses"]):
            if c["id"] == course_id:
                del data["courses"][idx]
                _save(data)
                return True
    return False

