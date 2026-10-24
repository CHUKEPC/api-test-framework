"""API Key authentication implementation."""

from __future__ import annotations

from typing import Any, Literal

from api_test_framework.auth.base import BaseAuth


class ApiKeyAuth(BaseAuth):
    """Applies API key authentication to request headers or query parameters."""

    def __init__(
        self,
        key_name: str,
        key_value: str,
        location: Literal["header", "query"] = "header",
    ) -> None:
        """Initialize API key credentials.

        Args:
            key_name: Header name (e.g. 'X-API-Key') or query param name (e.g. 'api_key').
            key_value: Secret key value.
            location: 'header' or 'query'.
        """
        self.key_name = key_name
        self.key_value = key_value
        self.location = location

    def apply(
        self,
        headers: dict[str, str],
        query_params: dict[str, Any],
    ) -> None:
        """Inject API key into headers or query parameters.

        Args:
            headers: Target headers dictionary.
            query_params: Target query parameters dictionary.
        """
        if self.location == "header":
            headers[self.key_name] = self.key_value
        else:
            query_params[self.key_name] = self.key_value
