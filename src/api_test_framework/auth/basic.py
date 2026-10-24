"""HTTP Basic Authentication implementation."""

from __future__ import annotations

import base64
from typing import Any

from api_test_framework.auth.base import BaseAuth


class BasicAuth(BaseAuth):
    """Applies HTTP Basic Auth header encoded in base64."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize Basic auth credentials.

        Args:
            username: HTTP basic auth username.
            password: HTTP basic auth password.
        """
        self.username = username
        self.password = password

    def apply(
        self,
        headers: dict[str, str],
        query_params: dict[str, Any],
    ) -> None:
        """Add Authorization Basic header.

        Args:
            headers: Target headers dictionary.
            query_params: Target query parameters dictionary (unused).
        """
        credentials = f"{self.username}:{self.password}".encode()
        encoded = base64.b64encode(credentials).decode("utf-8")
        headers["Authorization"] = f"Basic {encoded}"
