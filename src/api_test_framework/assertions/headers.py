"""HTTP response header assertions."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from api_test_framework.models.assertion import HeaderAssertionModel
from api_test_framework.models.result import AssertionResult

if TYPE_CHECKING:
    from collections.abc import Sequence


def _find_header_value(header_name: str, headers: dict[str, str]) -> str | None:
    """Case-insensitive search for header in headers dictionary."""
    target = header_name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value
    return None


def assert_single_header(
    rule: HeaderAssertionModel,
    actual_headers: dict[str, str],
) -> AssertionResult:
    """Evaluate a single header assertion rule against response headers.

    Args:
        rule: Assertion rule with header name, op, and expected value.
        actual_headers: Dict of headers received in response.

    Returns:
        AssertionResult representing outcome.
    """
    actual_val = _find_header_value(rule.name, actual_headers)

    if rule.op == "exists":
        expected_exists = True if rule.expected is None else bool(rule.expected)
        passed = (actual_val is not None) == expected_exists
        msg = (
            f"Header '{rule.name}' presence matches expected ({expected_exists})"
            if passed
            else f"Expected header '{rule.name}' to exist={expected_exists}, but present={actual_val is not None}"
        )
        return AssertionResult(
            name=f"header:{rule.name}",
            assertion_type="header",
            passed=passed,
            expected=expected_exists,
            actual=actual_val is not None,
            message=msg,
        )

    if actual_val is None:
        return AssertionResult(
            name=f"header:{rule.name}",
            assertion_type="header",
            passed=False,
            expected=rule.expected,
            actual=None,
            message=f"Header '{rule.name}' not found in response",
        )

    expected_str = str(rule.expected) if rule.expected is not None else ""

    if rule.op == "equals":
        passed = actual_val == expected_str
        msg = (
            f"Header '{rule.name}' matched expected value"
            if passed
            else f"Expected header '{rule.name}' to be '{expected_str}', got '{actual_val}'"
        )
    elif rule.op == "contains":
        passed = expected_str in actual_val
        msg = (
            f"Header '{rule.name}' contains '{expected_str}'"
            if passed
            else f"Expected header '{rule.name}' to contain '{expected_str}', but got '{actual_val}'"
        )
    elif rule.op == "regex":
        passed = bool(re.search(expected_str, actual_val))
        msg = (
            f"Header '{rule.name}' matches regex '{expected_str}'"
            if passed
            else f"Expected header '{rule.name}' to match regex '{expected_str}', but got '{actual_val}'"
        )
    else:
        passed = False
        msg = f"Unknown header comparison operator: '{rule.op}'"

    return AssertionResult(
        name=f"header:{rule.name}",
        assertion_type="header",
        passed=passed,
        expected=expected_str,
        actual=actual_val,
        message=msg,
    )


def assert_headers(
    rules: dict[str, Any] | Sequence[HeaderAssertionModel],
    actual_headers: dict[str, str],
) -> list[AssertionResult]:
    """Evaluate a dictionary or list of header assertions.

    Args:
        rules: Either a dict of {header_name: expected_value} or list of HeaderAssertionModel.
        actual_headers: HTTP response headers dict.

    Returns:
        List of AssertionResult objects.
    """
    results: list[AssertionResult] = []

    if isinstance(rules, dict):
        for header_name, expected in rules.items():
            if isinstance(expected, dict):
                op = expected.get("op", "equals")
                exp_val = expected.get("expected")
                rule = HeaderAssertionModel(name=header_name, op=op, expected=exp_val)
            else:
                rule = HeaderAssertionModel(name=header_name, op="equals", expected=str(expected))
            results.append(assert_single_header(rule, actual_headers))
    else:
        for rule in rules:
            results.append(assert_single_header(rule, actual_headers))

    return results
