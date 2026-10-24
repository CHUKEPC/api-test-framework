"""JSONPath assertions using jsonpath-ng."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from jsonpath_ng.ext.parser import parse as parse_jsonpath

from api_test_framework.models.assertion import JsonPathAssertionModel
from api_test_framework.models.result import AssertionResult

if TYPE_CHECKING:
    from collections.abc import Sequence


def assert_single_jsonpath(
    rule: JsonPathAssertionModel,
    actual_body: Any,
) -> AssertionResult:
    """Evaluate a single JSONPath assertion against body content.

    Args:
        rule: JsonPathAssertionModel with path, op, and expected value.
        actual_body: Parsed JSON structure.

    Returns:
        AssertionResult indicating success or failure.
    """
    if actual_body is None:
        return AssertionResult(
            name=f"jsonpath:{rule.path}",
            assertion_type="jsonpath",
            passed=False,
            expected=rule.expected,
            actual=None,
            message="Response body is None, cannot query JSONPath",
        )

    try:
        expr = parse_jsonpath(rule.path)
        matches = expr.find(actual_body)
    except Exception as exc:
        return AssertionResult(
            name=f"jsonpath:{rule.path}",
            assertion_type="jsonpath",
            passed=False,
            expected=rule.expected,
            actual=None,
            message=f"Invalid JSONPath expression '{rule.path}': {exc}",
        )

    if rule.op == "exists":
        expected_exists = True if rule.expected is None else bool(rule.expected)
        actual_exists = len(matches) > 0
        passed = actual_exists == expected_exists
        msg = (
            f"JSONPath '{rule.path}' existence verified (exists={actual_exists})"
            if passed
            else f"JSONPath '{rule.path}' expected exists={expected_exists}, got {actual_exists}"
        )
        return AssertionResult(
            name=f"jsonpath:{rule.path}",
            assertion_type="jsonpath",
            passed=passed,
            expected=expected_exists,
            actual=actual_exists,
            message=msg,
        )

    if not matches:
        return AssertionResult(
            name=f"jsonpath:{rule.path}",
            assertion_type="jsonpath",
            passed=False,
            expected=rule.expected,
            actual=None,
            message=f"JSONPath '{rule.path}' found no matching elements",
        )

    actual_val = matches[0].value

    if rule.op == "equals":
        passed = actual_val == rule.expected
        msg = (
            f"JSONPath '{rule.path}' equals expected value"
            if passed
            else f"JSONPath '{rule.path}' expected {rule.expected!r}, got {actual_val!r}"
        )
    elif rule.op == "not_equals":
        passed = actual_val != rule.expected
        msg = (
            f"JSONPath '{rule.path}' not equals {rule.expected!r}"
            if passed
            else f"JSONPath '{rule.path}' unexpectedly matched {rule.expected!r}"
        )
    elif rule.op == "contains":
        try:
            passed = rule.expected in actual_val
            msg = (
                f"JSONPath '{rule.path}' contains {rule.expected!r}"
                if passed
                else f"JSONPath '{rule.path}' does not contain {rule.expected!r}"
            )
        except TypeError:
            passed = False
            msg = f"JSONPath '{rule.path}' target of type {type(actual_val).__name__} does not support containment"
    elif rule.op == "regex":
        passed = bool(re.search(str(rule.expected), str(actual_val)))
        msg = (
            f"JSONPath '{rule.path}' matches regex pattern"
            if passed
            else f"JSONPath '{rule.path}' value '{actual_val}' failed regex '{rule.expected}'"
        )
    elif rule.op == "gt":
        passed = actual_val > rule.expected
        msg = (
            f"JSONPath '{rule.path}' value {actual_val} > {rule.expected}"
            if passed
            else f"JSONPath '{rule.path}' expected > {rule.expected}, got {actual_val}"
        )
    elif rule.op == "gte":
        passed = actual_val >= rule.expected
        msg = (
            f"JSONPath '{rule.path}' value {actual_val} >= {rule.expected}"
            if passed
            else f"JSONPath '{rule.path}' expected >= {rule.expected}, got {actual_val}"
        )
    elif rule.op == "lt":
        passed = actual_val < rule.expected
        msg = (
            f"JSONPath '{rule.path}' value {actual_val} < {rule.expected}"
            if passed
            else f"JSONPath '{rule.path}' expected < {rule.expected}, got {actual_val}"
        )
    elif rule.op == "lte":
        passed = actual_val <= rule.expected
        msg = (
            f"JSONPath '{rule.path}' value {actual_val} <= {rule.expected}"
            if passed
            else f"JSONPath '{rule.path}' expected <= {rule.expected}, got {actual_val}"
        )
    elif rule.op == "type":
        type_name = type(actual_val).__name__
        passed = type_name.lower() == str(rule.expected).lower()
        msg = (
            f"JSONPath '{rule.path}' has type '{type_name}'"
            if passed
            else f"JSONPath '{rule.path}' expected type '{rule.expected}', got '{type_name}'"
        )
    elif rule.op == "len":
        try:
            actual_len = len(actual_val)
            passed = actual_len == rule.expected
            msg = (
                f"JSONPath '{rule.path}' length is {actual_len}"
                if passed
                else f"JSONPath '{rule.path}' expected length {rule.expected}, got {actual_len}"
            )
        except TypeError:
            passed = False
            msg = f"JSONPath '{rule.path}' target of type {type(actual_val).__name__} does not have length"
    else:
        passed = False
        msg = f"Unknown JSONPath comparison operator: '{rule.op}'"

    return AssertionResult(
        name=f"jsonpath:{rule.path}",
        assertion_type="jsonpath",
        passed=passed,
        expected=rule.expected,
        actual=actual_val,
        message=msg,
    )


def assert_jsonpath(
    rules: dict[str, Any] | Sequence[JsonPathAssertionModel],
    actual_body: Any,
) -> list[AssertionResult]:
    """Evaluate JSONPath assertion rules against a response body.

    Args:
        rules: Mapping of path -> expected value/dict or list of JsonPathAssertionModel.
        actual_body: Decoded response payload.

    Returns:
        List of AssertionResult outcomes.
    """
    results: list[AssertionResult] = []

    if isinstance(rules, dict):
        for path, expected in rules.items():
            if isinstance(expected, dict) and ("op" in expected or "expected" in expected):
                op = expected.get("op", "equals")
                exp_val = expected.get("expected")
                rule = JsonPathAssertionModel(path=path, op=op, expected=exp_val)
            else:
                rule = JsonPathAssertionModel(path=path, op="equals", expected=expected)
            results.append(assert_single_jsonpath(rule, actual_body))
    else:
        for rule in rules:
            results.append(assert_single_jsonpath(rule, actual_body))

    return results
