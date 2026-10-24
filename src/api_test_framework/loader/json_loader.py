"""Loader for JSON-based test suite definitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from api_test_framework.exceptions import DSLValidationError
from api_test_framework.loader.validator import validate_test_suite_dict

if TYPE_CHECKING:
    from api_test_framework.models.test_suite import TestSuiteModel


def load_test_suite_from_json(content_or_path: str | Path) -> TestSuiteModel:
    """Load and validate a TestSuiteModel from a JSON string or file path.

    Args:
        content_or_path: File path to a .json file or raw JSON text string.

    Returns:
        Validated TestSuiteModel instance.

    Raises:
        DSLValidationError: If file is missing, JSON syntax is invalid, or schema fails.
    """
    json_text: str
    is_path = False

    if isinstance(content_or_path, Path):
        is_path = True
        path = content_or_path
    elif "\n" not in content_or_path and (
        content_or_path.endswith(".json") or Path(content_or_path).is_file()
    ):
        is_path = True
        path = Path(content_or_path)
    else:
        json_text = content_or_path

    if is_path:
        if not path.exists():
            raise DSLValidationError(f"Test suite JSON file not found: {path}")
        try:
            json_text = path.read_text(encoding="utf-8")
        except Exception as exc:
            raise DSLValidationError(f"Could not read JSON file '{path}': {exc}") from exc

    try:
        raw_data: Any = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise DSLValidationError(f"Invalid JSON syntax: {exc}") from exc

    if raw_data is None:
        raise DSLValidationError("JSON content is null")

    return validate_test_suite_dict(raw_data)
