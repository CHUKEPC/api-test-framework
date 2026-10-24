"""Loader for YAML-based test suite definitions."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from api_test_framework.exceptions import DSLValidationError
from api_test_framework.loader.validator import validate_test_suite_dict

if TYPE_CHECKING:
    from api_test_framework.models.test_suite import TestSuiteModel


def load_test_suite_from_yaml(content_or_path: str | Path) -> TestSuiteModel:
    """Load and validate a TestSuiteModel from a YAML string or file path.

    Args:
        content_or_path: Either file path to a .yaml/.yml file or raw YAML string.

    Returns:
        Validated TestSuiteModel instance.

    Raises:
        DSLValidationError: If file is missing, YAML syntax is invalid, or schema fails.
    """
    yaml_text: str
    is_path = False

    if isinstance(content_or_path, Path):
        is_path = True
        path = content_or_path
    elif "\n" not in content_or_path and (
        content_or_path.endswith((".yaml", ".yml")) or Path(content_or_path).is_file()
    ):
        is_path = True
        path = Path(content_or_path)
    else:
        yaml_text = content_or_path

    if is_path:
        if not path.exists():
            raise DSLValidationError(f"Test suite YAML file not found: {path}")
        try:
            yaml_text = path.read_text(encoding="utf-8")
        except Exception as exc:
            raise DSLValidationError(f"Could not read YAML file '{path}': {exc}") from exc

    try:
        raw_data: Any = yaml.safe_load(yaml_text)
    except yaml.YAMLError as exc:
        raise DSLValidationError(f"Invalid YAML syntax: {exc}") from exc

    if raw_data is None:
        raise DSLValidationError("YAML content is empty")

    return validate_test_suite_dict(raw_data)
