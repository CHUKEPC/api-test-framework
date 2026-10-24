"""Configuration management for api-test-framework."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class FrameworkConfig(BaseModel):
    """Runtime configuration settings for API testing framework."""

    base_url: str | None = Field(default=None, description="Default base URL for requests")
    timeout: float = Field(default=30.0, description="Default request timeout in seconds")
    verify_ssl: bool = Field(default=True, description="Whether to verify SSL certificates")
    retries: int = Field(default=0, description="Default number of retry attempts for requests")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")
    headers: dict[str, str] = Field(default_factory=dict, description="Global default headers")
    variables: dict[str, Any] = Field(default_factory=dict, description="Global default variables")
    follow_redirects: bool = Field(default=True, description="Whether to follow HTTP redirects")
    auth_token: str | None = Field(default=None, description="Global default bearer or auth token")
    env_file: str | None = Field(default=None, description="Path to environment variables file")

    @classmethod
    def from_env(cls, env_file: str | None = None) -> FrameworkConfig:
        """Create FrameworkConfig reading from environment variables and optional env file.

        Args:
            env_file: Optional path to a .env file to parse.

        Returns:
            Configured FrameworkConfig instance.
        """
        env_vars: dict[str, str] = {}
        if env_file:
            path = Path(env_file)
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#") and "=" in stripped:
                        key, val = stripped.split("=", 1)
                        env_vars[key.strip()] = val.strip().strip("'\"")

        base_url = env_vars.get("API_TEST_BASE_URL") or os.getenv("API_TEST_BASE_URL")
        auth_token = env_vars.get("API_TEST_AUTH_TOKEN") or os.getenv("API_TEST_AUTH_TOKEN")

        timeout_str = env_vars.get("API_TEST_TIMEOUT") or os.getenv("API_TEST_TIMEOUT")
        timeout = float(timeout_str) if timeout_str else 30.0

        verify_ssl_str = env_vars.get("API_TEST_VERIFY_SSL") or os.getenv(
            "API_TEST_VERIFY_SSL", "true"
        )
        verify_ssl = (verify_ssl_str or "true").lower() not in ("0", "false", "no", "off")

        retries_str = env_vars.get("API_TEST_RETRIES") or os.getenv("API_TEST_RETRIES")
        retries = int(retries_str) if retries_str else 0

        return cls(
            base_url=base_url,
            timeout=timeout,
            verify_ssl=verify_ssl,
            retries=retries,
            auth_token=auth_token,
            env_file=env_file,
        )
