"""Base abstraction for authentication handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAuth(ABC):
    """Abstract base class for all request authentication strategies."""

    @abstractmethod
    def apply(
        self,
        headers: dict[str, str],
        query_params: dict[str, Any],
    ) -> None:
        """Apply authentication credentials to request headers or query parameters.

        Args:
            headers: Target headers dictionary to modify in-place.
            query_params: Target query parameters dictionary to modify in-place.
        """
