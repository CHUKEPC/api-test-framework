"""Registry for custom user-defined assertion functions."""

from __future__ import annotations

from collections.abc import Callable

from api_test_framework.models.response import HttpResponseData
from api_test_framework.models.result import AssertionResult

CustomAssertionFn = Callable[[HttpResponseData], AssertionResult]

_CUSTOM_ASSERTIONS: dict[str, CustomAssertionFn] = {}


def register_custom_assertion(name: str, fn: CustomAssertionFn) -> None:
    """Register a custom assertion function under a unique name.

    Args:
        name: Identifier name for the custom assertion.
        fn: Callable accepting HttpResponseData and returning an AssertionResult.
    """
    _CUSTOM_ASSERTIONS[name] = fn


def get_custom_assertion(name: str) -> CustomAssertionFn | None:
    """Look up a registered custom assertion function.

    Args:
        name: Identifier name of the custom assertion.

    Returns:
        Registered callable or None if not found.
    """
    return _CUSTOM_ASSERTIONS.get(name)


def clear_custom_assertions() -> None:
    """Remove all registered custom assertion functions (useful for test isolation)."""
    _CUSTOM_ASSERTIONS.clear()
