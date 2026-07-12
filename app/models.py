"""Validation helpers and constants for Course records."""
from __future__ import annotations

from datetime import date
from typing import Any, Optional, Tuple

# Allowed lifecycle states for a course.
ALLOWED_STATUSES = ("Not Started", "In Progress", "Completed")
DEFAULT_STATUS = "Not Started"

# Whitelisted fields we persist. Anything else in the payload is dropped so the
# JSON file never accumulates "runaway" data.
ALLOWED_FIELDS = ("name", "description", "target_completion_date", "status")
REQUIRED_FIELDS = ("name", "description", "target_completion_date")


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def validate_course(
    payload: Any, partial: bool = False
) -> Tuple[Optional[dict], Optional[str]]:
    """Validate a course payload.

    Args:
        payload: The raw dict submitted by the client.
        partial: If True, missing required fields are allowed (used for PATCH).

    Returns:
        (clean_dict, None) on success, or (None, error_message) on failure.
    """
    if not isinstance(payload, dict):
        return None, "Request body must be a JSON object."

    clean: dict = {}

    # Enforce required fields on full create/replace.
    if not partial:
        for field in REQUIRED_FIELDS:
            if field not in payload:
                return None, f"Missing required field: '{field}'."

    # name
    if "name" in payload:
        if not _is_nonempty_str(payload["name"]):
            return None, "'name' must be a non-empty string."
        clean["name"] = payload["name"].strip()

    # description
    if "description" in payload:
        if not isinstance(payload["description"], str):
            return None, "'description' must be a string."
        clean["description"] = payload["description"].strip()

    # target_completion_date (ISO YYYY-MM-DD)
    if "target_completion_date" in payload:
        raw = payload["target_completion_date"]
        if not isinstance(raw, str):
            return None, "'target_completion_date' must be a string (YYYY-MM-DD)."
        try:
            date.fromisoformat(raw)
        except ValueError:
            return None, "'target_completion_date' must be in YYYY-MM-DD format."
        clean["target_completion_date"] = raw

    # status (optional; defaults applied at create time)
    if "status" in payload:
        if payload["status"] not in ALLOWED_STATUSES:
            return (
                None,
                f"'status' must be one of: {', '.join(ALLOWED_STATUSES)}.",
            )
        clean["status"] = payload["status"]

    return clean, None

