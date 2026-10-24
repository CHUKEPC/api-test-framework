"""Model representing executed HTTP response data."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HttpResponseData(BaseModel):
    """Captured response data from an executed HTTP request."""

    status_code: int = Field(description="HTTP status code received")
    headers: dict[str, str] = Field(
        default_factory=dict, description="Normalized response headers"
    )
    body: Any = Field(default=None, description="Decoded JSON payload or parsed content")
    text: str = Field(default="", description="Raw response text body")
    elapsed_seconds: float = Field(
        default=0.0, description="Round-trip time of request in seconds"
    )
    url: str = Field(default="", description="Final URL after any redirects")
    method: str = Field(default="GET", description="HTTP method used for request")
    cookies: dict[str, str] = Field(default_factory=dict, description="Response cookies")

    model_config = {
        "arbitrary_types_allowed": True,
    }
