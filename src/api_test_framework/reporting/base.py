"""Base reporter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from api_test_framework.models.result import TestSuiteResult


class BaseReporter(ABC):
    """Abstract interface for test execution report formatters."""

    @abstractmethod
    def generate(self, results: Sequence[TestSuiteResult]) -> str:
        """Generate formatted report string from test suite results.

        Args:
            results: Sequence of completed TestSuiteResult models.

        Returns:
            Rendered report content string.
        """
