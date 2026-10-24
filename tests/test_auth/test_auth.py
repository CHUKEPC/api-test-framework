"""Tests for authentication strategies and factory functions."""

from __future__ import annotations

import base64

import httpx
import pytest

from api_test_framework.auth import (
    ApiKeyAuth,
    BasicAuth,
    BearerAuth,
    OAuth2ClientCredentials,
    create_auth_handler,
)
from api_test_framework.exceptions import AuthenticationError, ConfigurationError
from api_test_framework.models.request import AuthModel


def test_bearer_auth() -> None:
    """Verify BearerAuth sets Authorization header."""
    auth = BearerAuth("my-secret-token")
    headers: dict[str, str] = {}
    params: dict[str, str] = {}
    auth.apply(headers, params)
    assert headers["Authorization"] == "Bearer my-secret-token"
    assert params == {}


def test_basic_auth() -> None:
    """Verify BasicAuth encodes credentials in base64."""
    auth = BasicAuth("admin", "p@ssword")
    headers: dict[str, str] = {}
    params: dict[str, str] = {}
    auth.apply(headers, params)

    encoded = base64.b64encode(b"admin:p@ssword").decode()
    assert headers["Authorization"] == f"Basic {encoded}"


def test_api_key_auth_header() -> None:
    """Verify ApiKeyAuth injects into headers."""
    auth = ApiKeyAuth(key_name="X-API-Key", key_value="abc1234", location="header")
    headers: dict[str, str] = {}
    params: dict[str, str] = {}
    auth.apply(headers, params)
    assert headers["X-API-Key"] == "abc1234"
    assert params == {}


def test_api_key_auth_query() -> None:
    """Verify ApiKeyAuth injects into query params."""
    auth = ApiKeyAuth(key_name="api_token", key_value="secret_key", location="query")
    headers: dict[str, str] = {}
    params: dict[str, str] = {}
    auth.apply(headers, params)
    assert headers == {}
    assert params["api_token"] == "secret_key"


def test_oauth2_client_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify OAuth2 Client Credentials requests and caches token."""

    def mock_post(client: httpx.Client, url: str, **kwargs: httpx.Response) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={"access_token": "oauth_token_777", "token_type": "Bearer"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    auth = OAuth2ClientCredentials(
        token_url="https://auth.example.com/oauth/token",
        client_id="client123",
        client_secret="secret456",
        scope="read:all",
    )

    headers: dict[str, str] = {}
    params: dict[str, str] = {}
    auth.apply(headers, params)
    assert headers["Authorization"] == "Bearer oauth_token_777"

    # Second call should use cached token without making another HTTP call
    headers2: dict[str, str] = {}
    auth.apply(headers2, params)
    assert headers2["Authorization"] == "Bearer oauth_token_777"


def test_oauth2_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify AuthenticationError is raised when token endpoint errors."""

    def mock_post_err(client: httpx.Client, url: str, **kwargs: httpx.Response) -> httpx.Response:
        return httpx.Response(
            status_code=401,
            json={"error": "invalid_client"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.Client, "post", mock_post_err)

    auth = OAuth2ClientCredentials(
        token_url="https://auth.example.com/oauth/token",
        client_id="client123",
        client_secret="bad_secret",
    )
    with pytest.raises(AuthenticationError, match="Failed to fetch OAuth2 token"):
        auth.get_token()


def test_create_auth_handler_factory() -> None:
    """Verify create_auth_handler factory with all model types."""
    assert create_auth_handler(None) is None

    b_handler = create_auth_handler(AuthModel(type="bearer", token="tok"))
    assert isinstance(b_handler, BearerAuth)

    basic_handler = create_auth_handler(AuthModel(type="basic", username="u", password="p"))
    assert isinstance(basic_handler, BasicAuth)

    key_handler = create_auth_handler(AuthModel(type="api_key", key_name="K", key_value="V"))
    assert isinstance(key_handler, ApiKeyAuth)

    oauth_handler = create_auth_handler(
        AuthModel(type="oauth2", token_url="http://u", client_id="c", client_secret="s")
    )
    assert isinstance(oauth_handler, OAuth2ClientCredentials)


def test_create_auth_handler_validation_errors() -> None:
    """Verify ConfigurationError on missing required fields."""
    with pytest.raises(ConfigurationError, match="requires 'token'"):
        create_auth_handler(AuthModel(type="bearer"))

    with pytest.raises(ConfigurationError, match="requires both"):
        create_auth_handler(AuthModel(type="basic", username="u"))

    with pytest.raises(ConfigurationError, match="requires 'key_value'"):
        create_auth_handler(AuthModel(type="api_key"))

    with pytest.raises(ConfigurationError, match="requires 'token_url'"):
        create_auth_handler(AuthModel(type="oauth2"))
