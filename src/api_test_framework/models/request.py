"""Models defining HTTP request structure and authentication settings."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
AuthType = Literal["bearer", "basic", "api_key", "oauth2"]


class AuthModel(BaseModel):
    """Authentication configuration model for test requests and suites."""

    type: AuthType = Field(description="Authentication scheme type")
    token: str | None = Field(default=None, description="Bearer token or API token value")
    username: str | None = Field(default=None, description="Username for HTTP Basic Auth")
    password: str | None = Field(default=None, description="Password for HTTP Basic Auth")
    key_name: str | None = Field(default=None, description="API Key name (e.g. X-API-Key)")
    key_value: str | None = Field(default=None, description="API Key value")
    location: Literal["header", "query"] = Field(
        default="header", description="Where to inject API key"
    )
    # OAuth2 client credentials fields
    token_url: str | None = Field(default=None, description="OAuth2 token endpoint URL")
    client_id: str | None = Field(default=None, description="OAuth2 client ID")
    client_secret: str | None = Field(default=None, description="OAuth2 client secret")
    scope: str | None = Field(default=None, description="OAuth2 requested scope")


class HttpRequestModel(BaseModel):
    """Declarative HTTP request specification."""

    method: HttpMethod = Field(default="GET", description="HTTP verb")
    url: str = Field(description="Target URL (relative or absolute)")
    path_params: dict[str, Any] = Field(
        default_factory=dict, description="URL path parameter substitutions"
    )
    query_params: dict[str, Any] = Field(
        default_factory=dict, description="URL query string parameters"
    )
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP request headers")
    cookies: dict[str, str] = Field(default_factory=dict, description="Request cookies")
    json_body: Any = Field(default=None, alias="json", description="JSON request payload")
    data: dict[str, Any] | str | None = Field(
        default=None, description="Form data or raw string body"
    )
    auth: AuthModel | None = Field(
        default=None, description="Optional request-specific authentication"
    )
    timeout: float | None = Field(default=None, description="Optional custom timeout in seconds")
    verify_ssl: bool | None = Field(
        default=None, description="Whether SSL certificates are checked"
    )
    follow_redirects: bool | None = Field(
        default=None, description="Whether to follow 3xx redirects"
    )

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
