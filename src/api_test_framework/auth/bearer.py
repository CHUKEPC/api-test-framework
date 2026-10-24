"""Bearer token authentication implementation."""

from __future__ import annotations

from typing import Any

from api_test_framework.auth.base import BaseAuth


class BearerAuth(BaseAuth):
    """Applies HTTP Authorization header with Bearer token scheme."""

    def __init__(self, token: str) -> None:
        """Initialize Bearer token auth.

        Args:
            token: Bearer token string (without 'Bearer ' prefix).
        """
        self.token = token.strip()

    def apply(
        self,
        headers: dict[str, str],
        query_params: dict[str, Any],
    ) -> None:
        """Add Authorization Bearer header.

        Args:
            headers: Target headers dictionary.
            query_params: Target query parameters dictionary (unused).
        """
        headers["Authorization"] = f"Bearer {self.token}"
