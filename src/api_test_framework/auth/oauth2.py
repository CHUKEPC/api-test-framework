"""OAuth2 client credentials authentication helper."""

from __future__ import annotations

from typing import Any

import httpx

from api_test_framework.auth.base import BaseAuth
from api_test_framework.exceptions import AuthenticationError


class OAuth2ClientCredentials(BaseAuth):
    """Obtains and caches Bearer tokens using OAuth2 client credentials flow."""

    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scope: str | None = None,
        cached_token: str | None = None,
    ) -> None:
        """Initialize OAuth2 Client Credentials helper.

        Args:
            token_url: Endpoint URL to request access token from.
            client_id: OAuth2 client identifier.
            client_secret: OAuth2 client secret key.
            scope: Optional scope string requested.
            cached_token: Optional pre-existing token string.
        """
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self._access_token: str | None = cached_token

    def get_token(self) -> str:
        """Fetch token from token endpoint or return cached token.

        Returns:
            Bearer access token.

        Raises:
            AuthenticationError: If token request fails or response is invalid.
        """
        if self._access_token:
            return self._access_token

        payload: dict[str, str] = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.scope:
            payload["scope"] = self.scope

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(self.token_url, data=payload)
                response.raise_for_status()
                data = response.json()
                token = data.get("access_token")
                if not token:
                    raise AuthenticationError("OAuth2 response missing 'access_token' field")
                self._access_token = str(token)
                return self._access_token
        except Exception as exc:
            raise AuthenticationError(
                f"Failed to fetch OAuth2 token from '{self.token_url}': {exc}"
            ) from exc

    def apply(
        self,
        headers: dict[str, str],
        query_params: dict[str, Any],
    ) -> None:
        """Inject Bearer token header obtained from OAuth2 flow.

        Args:
            headers: Target headers dictionary.
            query_params: Target query parameters dictionary (unused).
        """
        token = self.get_token()
        headers["Authorization"] = f"Bearer {token}"
