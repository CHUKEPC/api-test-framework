"""Assertions on response body content and structure."""

from __future__ import annotations

import re
from typing import Any

from api_test_framework.models.result import AssertionResult


def assert_body_exact(expected: Any, actual: Any) -> AssertionResult:
    """Assert that entire response body exactly matches expected value.

    Args:
        expected: Expected body value (dict, list, str, etc.).
        actual: Actual parsed or text body.

    Returns:
        AssertionResult indicating exact equality.
    """
    passed = expected == actual
    message = (
        "Response body matches expected structure exactly"
        if passed
        else f"Response body mismatch. Expected: {expected!r}, Got: {actual!r}"
    )
    return AssertionResult(
        name="body:exact",
        assertion_type="body",
        passed=passed,
        expected=expected,
        actual=actual,
        message=message,
    )


def assert_body_contains(substring: str, actual_text: str) -> AssertionResult:
    """Assert that the response body text contains a given substring.

    Args:
        substring: Expected substring.
        actual_text: Full response body text.

    Returns:
        AssertionResult.
    """
    passed = substring in actual_text
    message = (
        f"Response text contains expected substring '{substring}'"
        if passed
        else f"Response text does not contain substring '{substring}'"
    )
    return AssertionResult(
        name="body:contains",
        assertion_type="body",
        passed=passed,
        expected=substring,
        actual=actual_text[:200] + ("..." if len(actual_text) > 200 else ""),
        message=message,
    )


def assert_body_regex(pattern: str, actual_text: str) -> AssertionResult:
    """Assert that response body text matches a regular expression pattern.

    Args:
        pattern: Regex pattern string.
        actual_text: Full response body text.

    Returns:
        AssertionResult.
    """
    passed = bool(re.search(pattern, actual_text))
    message = (
        f"Response text matched regex pattern '{pattern}'"
        if passed
        else f"Response text failed to match regex pattern '{pattern}'"
    )
    return AssertionResult(
        name="body:regex",
        assertion_type="body",
        passed=passed,
        expected=pattern,
        actual=actual_text[:200] + ("..." if len(actual_text) > 200 else ""),
        message=message,
    )


def _deep_compare(expected: Any, actual: Any, path: str = "$") -> list[AssertionResult]:
    """Recursively check that expected data is a subset of actual data."""
    results: list[AssertionResult] = []

    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            results.append(
                AssertionResult(
                    name=f"body:{path}",
                    assertion_type="body",
                    passed=False,
                    expected="dict",
                    actual=type(actual).__name__,
                    message=f"At {path}: expected dict, got {type(actual).__name__}",
                )
            )
            return results

        for key, exp_val in expected.items():
            curr_path = f"{path}.{key}"
            if key not in actual:
                results.append(
                    AssertionResult(
                        name=f"body:{curr_path}",
                        assertion_type="body",
                        passed=False,
                        expected=exp_val,
                        actual=None,
                        message=f"Missing expected key '{key}' at {path}",
                    )
                )
            else:
                results.extend(_deep_compare(exp_val, actual[key], curr_path))

    elif isinstance(expected, list):
        if not isinstance(actual, list):
            results.append(
                AssertionResult(
                    name=f"body:{path}",
                    assertion_type="body",
                    passed=False,
                    expected="list",
                    actual=type(actual).__name__,
                    message=f"At {path}: expected list, got {type(actual).__name__}",
                )
            )
            return results

        if len(expected) != len(actual):
            results.append(
                AssertionResult(
                    name=f"body:{path}:length",
                    assertion_type="body",
                    passed=False,
                    expected=len(expected),
                    actual=len(actual),
                    message=f"At {path}: list length mismatch (expected {len(expected)}, got {len(actual)})",
                )
            )

        for idx, exp_item in enumerate(expected):
            curr_path = f"{path}[{idx}]"
            if idx < len(actual):
                results.extend(_deep_compare(exp_item, actual[idx], curr_path))

    else:
        passed = expected == actual
        results.append(
            AssertionResult(
                name=f"body:{path}",
                assertion_type="body",
                passed=passed,
                expected=expected,
                actual=actual,
                message=(
                    f"At {path}: value matched"
                    if passed
                    else f"At {path}: expected {expected!r}, got {actual!r}"
                ),
            )
        )

    return results


def assert_body_deep(expected: Any, actual: Any) -> list[AssertionResult]:
    """Perform recursive subset comparison between expected and actual data structures.

    Args:
        expected: Expected subset dictionary, list, or primitive.
        actual: Received data structure.

    Returns:
        List of AssertionResult checks for all evaluated nodes.
    """
    return _deep_compare(expected, actual)
