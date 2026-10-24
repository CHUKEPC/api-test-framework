"""Authentication helper classes and factory functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from api_test_framework.auth.api_key import ApiKeyAuth
from api_test_framework.auth.base import BaseAuth
from api_test_framework.auth.basic import BasicAuth
from api_test_framework.auth.bearer import BearerAuth
from api_test_framework.auth.oauth2 import OAuth2ClientCredentials
from api_test_framework.exceptions import ConfigurationError

if TYPE_CHECKING:
    from api_test_framework.models.request import AuthModel


def create_auth_handler(auth_model: AuthModel | None) -> BaseAuth | None:
    """Instantiate appropriate BaseAuth implementation from AuthModel configuration.

    Args:
        auth_model: Declarative authentication configuration.

    Returns:
        BaseAuth instance or None if no auth configured.

    Raises:
        ConfigurationError: If required fields for chosen auth type are missing.
    """
    if auth_model is None:
        return None

    auth_type = auth_model.type.lower()
    if auth_type == "bearer":
        if not auth_model.token:
            raise ConfigurationError("Bearer auth requires 'token'")
        return BearerAuth(token=auth_model.token)

    if auth_type == "basic":
        if auth_model.username is None or auth_model.password is None:
            raise ConfigurationError("Basic auth requires both 'username' and 'password'")
        return BasicAuth(username=auth_model.username, password=auth_model.password)

    if auth_type == "api_key":
        key_name = auth_model.key_name or "X-API-Key"
        key_value = auth_model.key_value or auth_model.token or ""
        if not key_value:
            raise ConfigurationError("API key auth requires 'key_value' or 'token'")
        return ApiKeyAuth(
            key_name=key_name,
            key_value=key_value,
            location=auth_model.location,
        )

    if auth_type == "oauth2":
        if not auth_model.token_url or not auth_model.client_id or not auth_model.client_secret:
            raise ConfigurationError(
                "OAuth2 auth requires 'token_url', 'client_id', and 'client_secret'"
            )
        return OAuth2ClientCredentials(
            token_url=auth_model.token_url,
            client_id=auth_model.client_id,
            client_secret=auth_model.client_secret,
            scope=auth_model.scope,
            cached_token=auth_model.token,
        )

    raise ConfigurationError(f"Unsupported auth type: '{auth_model.type}'")


__all__ = [
    "ApiKeyAuth",
    "BaseAuth",
    "BasicAuth",
    "BearerAuth",
    "OAuth2ClientCredentials",
    "create_auth_handler",
]
