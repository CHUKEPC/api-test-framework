"""JSON Schema validation assertions using jsonschema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from api_test_framework.models.result import AssertionResult


def assert_json_schema(
    schema_def: dict[str, Any] | str,
    actual_body: Any,
) -> AssertionResult:
    """Validate that actual response body adheres to the specified JSON Schema.

    Args:
        schema_def: Either a Python dict representing schema or a file path string.
        actual_body: Received JSON payload to validate.

    Returns:
        AssertionResult indicating schema conformity.
    """
    if actual_body is None:
        return AssertionResult(
            name="schema:json_schema",
            assertion_type="schema",
            passed=False,
            expected=schema_def,
            actual=None,
            message="Response body is None, cannot validate against JSON schema",
        )

    schema: dict[str, Any]
    if isinstance(schema_def, str):
        schema_path = Path(schema_def)
        if not schema_path.exists():
            return AssertionResult(
                name="schema:json_schema",
                assertion_type="schema",
                passed=False,
                expected=schema_def,
                actual=None,
                message=f"Schema file not found at path: {schema_def}",
            )
        content = schema_path.read_text(encoding="utf-8")
        try:
            if schema_def.endswith((".yaml", ".yml")):
                schema = yaml.safe_load(content)
            else:
                schema = json.loads(content)
        except Exception as exc:
            return AssertionResult(
                name="schema:json_schema",
                assertion_type="schema",
                passed=False,
                expected=schema_def,
                actual=None,
                message=f"Failed to parse schema file: {exc}",
            )
    else:
        schema = schema_def

    try:
        validator = jsonschema.Draft202012Validator(schema)
        errors = list(validator.iter_errors(actual_body))
        if not errors:
            return AssertionResult(
                name="schema:json_schema",
                assertion_type="schema",
                passed=True,
                expected="Valid JSON Schema",
                actual="Valid JSON Schema",
                message="Response body conforms to JSON Schema",
            )

        err_messages = [f"- {err.message} at '{err.json_path}'" for err in errors[:5]]
        if len(errors) > 5:
            err_messages.append(f"... and {len(errors) - 5} more schema error(s)")

        return AssertionResult(
            name="schema:json_schema",
            assertion_type="schema",
            passed=False,
            expected=schema,
            actual=actual_body,
            message="JSON Schema validation failed:\n" + "\n".join(err_messages),
        )

    except Exception as exc:
        return AssertionResult(
            name="schema:json_schema",
            assertion_type="schema",
            passed=False,
            expected=schema,
            actual=actual_body,
            message=f"JSON Schema validation error: {exc}",
        )
