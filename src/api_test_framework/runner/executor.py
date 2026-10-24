"""HTTP request executor with retries, timing, and response mapping."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

import httpx

from api_test_framework.auth import create_auth_handler
from api_test_framework.config import FrameworkConfig
from api_test_framework.exceptions import HttpRequestError
from api_test_framework.models.response import HttpResponseData

if TYPE_CHECKING:
    from api_test_framework.models.request import HttpRequestModel

logger = logging.getLogger(__name__)


class HttpExecutor:
    """Executes HTTP requests with retries, timeouts, cookies, and timing."""

    def __init__(self, config: FrameworkConfig | None = None) -> None:
        """Initialize executor with optional configuration.

        Args:
            config: FrameworkConfig instance.
        """
        self.config = config or FrameworkConfig()

    def _prepare_url(
        self,
        url: str,
        path_params: dict[str, Any],
        base_url: str | None,
    ) -> str:
        """Substitute path parameters and resolve against base URL if relative.

        Args:
            url: Request URL path or absolute URL.
            path_params: Dictionary of path parameter substitutions.
            base_url: Optional base URL prefix.

        Returns:
            Fully resolved URL string.
        """
        formatted_url = url
        for key, val in path_params.items():
            formatted_url = formatted_url.replace(f"{{{key}}}", str(val))
            formatted_url = formatted_url.replace(f":{key}", str(val))

        target_base = base_url or self.config.base_url
        if target_base and not (
            formatted_url.startswith("http://") or formatted_url.startswith("https://")
        ):
            # Ensure proper urljoin without stripping path segments
            if not target_base.endswith("/"):
                target_base += "/"
            if formatted_url.startswith("/"):
                formatted_url = formatted_url.lstrip("/")
            return urljoin(target_base, formatted_url)

        return formatted_url

    def _prepare_request_kwargs(
        self,
        request: HttpRequestModel,
        base_url: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Construct URL and kwargs dictionary for httpx request call."""
        url = self._prepare_url(request.url, request.path_params, base_url)

        headers = dict(self.config.headers)
        headers.update(request.headers)

        query_params = dict(request.query_params)

        # Apply authentication helper
        if request.auth is not None:
            auth_handler = create_auth_handler(request.auth)
            if auth_handler:
                auth_handler.apply(headers, query_params)
        elif self.config.auth_token:
            headers.setdefault("Authorization", f"Bearer {self.config.auth_token}")

        timeout = request.timeout if request.timeout is not None else self.config.timeout
        follow_redirects = (
            request.follow_redirects
            if request.follow_redirects is not None
            else self.config.follow_redirects
        )

        kwargs: dict[str, Any] = {
            "headers": headers,
            "params": query_params,
            "timeout": timeout,
            "follow_redirects": follow_redirects,
        }
        if request.cookies:
            kwargs["cookies"] = request.cookies

        if request.json_body is not None:
            kwargs["json"] = request.json_body
        elif request.data is not None:
            kwargs["data"] = request.data

        return url, kwargs

    async def execute_request(
        self,
        request: HttpRequestModel,
        base_url: str | None = None,
        retries: int | None = None,
        retry_delay: float | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> HttpResponseData:
        """Execute HTTP request asynchronously with automatic retry logic.

        Args:
            request: HttpRequestModel specification.
            base_url: Optional suite or global base URL override.
            retries: Number of retries on failure (defaults to config).
            retry_delay: Delay between retries in seconds.
            client: Optional reusable httpx.AsyncClient.

        Returns:
            Captured HttpResponseData.

        Raises:
            HttpRequestError: If all attempts fail.
        """
        max_attempts = (retries if retries is not None else self.config.retries) + 1
        delay = retry_delay if retry_delay is not None else self.config.retry_delay
        verify_ssl = (
            request.verify_ssl if request.verify_ssl is not None else self.config.verify_ssl
        )

        url, kwargs = self._prepare_request_kwargs(request, base_url)

        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            start_time = time.perf_counter()
            try:
                if client is not None:
                    httpx_resp = await client.request(request.method, url, **kwargs)
                else:
                    async with httpx.AsyncClient(verify=verify_ssl) as fresh_client:
                        httpx_resp = await fresh_client.request(request.method, url, **kwargs)

                elapsed = time.perf_counter() - start_time

                # Attempt parsing JSON body if possible
                body_content: Any = None
                try:
                    body_content = httpx_resp.json()
                except Exception:
                    body_content = None

                try:
                    cookies_dict = dict(httpx_resp.cookies)
                except Exception:
                    cookies_dict = {}

                return HttpResponseData(
                    status_code=httpx_resp.status_code,
                    headers=dict(httpx_resp.headers),
                    body=body_content,
                    text=httpx_resp.text,
                    elapsed_seconds=elapsed,
                    url=str(httpx_resp.url),
                    method=request.method,
                    cookies=cookies_dict,
                )

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "HTTP request failed on attempt %d/%d: %s %s: %s",
                    attempt,
                    max_attempts,
                    request.method,
                    url,
                    exc,
                )
                if attempt < max_attempts:
                    await asyncio.sleep(delay)

        raise HttpRequestError(
            f"HTTP {request.method} {url} failed after {max_attempts} attempts: {last_error}"
        ) from last_error

    def execute_request_sync(
        self,
        request: HttpRequestModel,
        base_url: str | None = None,
        retries: int | None = None,
        retry_delay: float | None = None,
    ) -> HttpResponseData:
        """Synchronously execute HTTP request with automatic retry logic.

        Args:
            request: HttpRequestModel specification.
            base_url: Optional base URL override.
            retries: Number of retries on failure.
            retry_delay: Delay between retries in seconds.

        Returns:
            Captured HttpResponseData.
        """
        max_attempts = (retries if retries is not None else self.config.retries) + 1
        delay = retry_delay if retry_delay is not None else self.config.retry_delay
        verify_ssl = (
            request.verify_ssl if request.verify_ssl is not None else self.config.verify_ssl
        )

        url, kwargs = self._prepare_request_kwargs(request, base_url)
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            start_time = time.perf_counter()
            try:
                with httpx.Client(verify=verify_ssl) as client:
                    httpx_resp = client.request(request.method, url, **kwargs)

                elapsed = time.perf_counter() - start_time

                body_content: Any = None
                try:
                    body_content = httpx_resp.json()
                except Exception:
                    body_content = None

                try:
                    cookies_dict = dict(httpx_resp.cookies)
                except Exception:
                    cookies_dict = {}

                return HttpResponseData(
                    status_code=httpx_resp.status_code,
                    headers=dict(httpx_resp.headers),
                    body=body_content,
                    text=httpx_resp.text,
                    elapsed_seconds=elapsed,
                    url=str(httpx_resp.url),
                    method=request.method,
                    cookies=cookies_dict,
                )
            except Exception as exc:
                last_error = exc
                if attempt < max_attempts:
                    time.sleep(delay)

        raise HttpRequestError(
            f"HTTP {request.method} {url} failed after {max_attempts} attempts: {last_error}"
        ) from last_error
