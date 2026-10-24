"""Loading and parsing utilities for YAML and JSON test suites."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from api_test_framework.exceptions import DSLValidationError
from api_test_framework.loader.json_loader import load_test_suite_from_json
from api_test_framework.loader.validator import validate_test_suite_dict
from api_test_framework.loader.yaml_loader import load_test_suite_from_yaml

if TYPE_CHECKING:
    from api_test_framework.models.test_suite import TestSuiteModel


def load_test_suite(path_or_str: str | Path) -> TestSuiteModel:
    """Load test suite from YAML or JSON path based on file extension.

    Args:
        path_or_str: Path to file or raw serialized text.

    Returns:
        Validated TestSuiteModel.

    Raises:
        DSLValidationError: If file extension is unsupported or content is invalid.
    """
    path_str = str(path_or_str).lower()
    if path_str.endswith((".yaml", ".yml")):
        return load_test_suite_from_yaml(path_or_str)
    if path_str.endswith(".json"):
        return load_test_suite_from_json(path_or_str)

    # If raw content or unknown extension, attempt YAML first, then JSON
    try:
        return load_test_suite_from_yaml(path_or_str)
    except DSLValidationError:
        try:
            return load_test_suite_from_json(path_or_str)
        except DSLValidationError as exc:
            raise DSLValidationError(
                f"Failed to parse test suite as either YAML or JSON: {exc}"
            ) from exc


__all__ = [
    "load_test_suite",
    "load_test_suite_from_json",
    "load_test_suite_from_yaml",
    "validate_test_suite_dict",
]
