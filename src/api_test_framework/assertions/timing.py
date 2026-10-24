"""Response duration and timing assertions."""

from __future__ import annotations

from api_test_framework.models.result import AssertionResult


def assert_max_duration(
    max_seconds: float,
    actual_seconds: float,
) -> AssertionResult:
    """Assert that request execution duration did not exceed maximum threshold.

    Args:
        max_seconds: Maximum allowed latency in seconds.
        actual_seconds: Elapsed duration of the request in seconds.

    Returns:
        AssertionResult indicating timing performance.
    """
    passed = actual_seconds <= max_seconds
    actual_ms = round(actual_seconds * 1000, 2)
    max_ms = round(max_seconds * 1000, 2)

    message = (
        f"Response duration {actual_ms}ms within limit of {max_ms}ms"
        if passed
        else f"Response duration {actual_ms}ms exceeded maximum allowed {max_ms}ms"
    )

    return AssertionResult(
        name="timing:max_duration",
        assertion_type="timing",
        passed=passed,
        expected=f"<= {max_seconds}s",
        actual=f"{actual_seconds}s",
        message=message,
    )
