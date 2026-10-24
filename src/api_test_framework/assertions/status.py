"""HTTP status code assertion logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from api_test_framework.models.result import AssertionResult

if TYPE_CHECKING:
    from collections.abc import Sequence


def assert_status_code(
    expected: int | Sequence[int],
    actual: int,
) -> AssertionResult:
    """Assert that the received HTTP status code matches expected code(s).

    Args:
        expected: Single integer or sequence of allowed status codes.
        actual: Received HTTP status code from response.

    Returns:
        AssertionResult indicating success or failure with context.
    """
    if isinstance(expected, int):
        passed = actual == expected
        message = (
            f"Status code matched expected {expected}"
            if passed
            else f"Expected status code {expected}, got {actual}"
        )
    else:
        allowed = list(expected)
        passed = actual in allowed
        message = (
            f"Status code {actual} is in allowed list {allowed}"
            if passed
            else f"Expected status code in {allowed}, got {actual}"
        )

    return AssertionResult(
        name="status_code",
        assertion_type="status",
        passed=passed,
        expected=expected,
        actual=actual,
        message=message,
    )
