"""Validation of test suite specifications against domain models."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from api_test_framework.exceptions import DSLValidationError
from api_test_framework.models.test_suite import TestSuiteModel


def validate_test_suite_dict(data: Any) -> TestSuiteModel:
    """Validate raw dictionary data against the TestSuiteModel schema.

    Args:
        data: Parsed dictionary from YAML or JSON.

    Returns:
        Validated TestSuiteModel instance.

    Raises:
        DSLValidationError: If data is not a dictionary or violates schema.
    """
    if not isinstance(data, dict):
        raise DSLValidationError(
            f"Expected root of test definition to be a mapping/dict, got {type(data).__name__}"
        )

    try:
        return TestSuiteModel.model_validate(data)
    except ValidationError as exc:
        formatted_errors: list[str] = []
        for error in exc.errors():
            loc = " -> ".join(str(elem) for elem in error["loc"])
            formatted_errors.append(f"Field '{loc}': {error['msg']}")
        msg = "DSL schema validation failed:\n" + "\n".join(formatted_errors)
        raise DSLValidationError(msg) from exc
