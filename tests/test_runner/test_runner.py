"""Tests for HttpExecutor, SuiteExecutor, and ParallelExecutor."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from api_test_framework.config import FrameworkConfig
from api_test_framework.exceptions import HttpRequestError
from api_test_framework.models.assertion import AssertionModel, JsonPathAssertionModel
from api_test_framework.models.request import HttpRequestModel
from api_test_framework.models.test_case import TestCaseModel, VariableExtractionModel
from api_test_framework.models.test_suite import HookModel, TestSuiteModel
from api_test_framework.runner.chain import SuiteExecutor
from api_test_framework.runner.executor import HttpExecutor
from api_test_framework.runner.parallel import ParallelExecutor


@pytest.mark.asyncio
async def test_executor_get_and_post() -> None:
    """Verify executing GET and POST requests with path and query parameters."""

    def mock_handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path == "/users/42":
            assert request.url.params.get("active") == "true"
            return httpx.Response(200, json={"id": 42, "name": "Alice"})
        if request.method == "POST" and request.url.path == "/users":
            content = request.read().decode()
            assert "Bob" in content
            return httpx.Response(201, json={"id": 43, "name": "Bob"})
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        executor = HttpExecutor(FrameworkConfig(base_url="https://api.test"))

        # Test GET with path_params & query_params
        req_get = HttpRequestModel(
            method="GET",
            url="/users/{user_id}",
            path_params={"user_id": 42},
            query_params={"active": "true"},
        )
        resp_get = await executor.execute_request(req_get, client=client)
        assert resp_get.status_code == 200
        assert resp_get.body["name"] == "Alice"

        # Test POST with json body
        req_post = HttpRequestModel(
            method="POST",
            url="/users",
            json={"name": "Bob"},
        )
        resp_post = await executor.execute_request(req_post, client=client)
        assert resp_post.status_code == 201
        assert resp_post.body["id"] == 43


@pytest.mark.asyncio
async def test_executor_retry_logic() -> None:
    """Verify HttpExecutor retries on failure and eventually succeeds or fails."""
    attempts = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise httpx.ConnectError("Connection refused")
        return httpx.Response(200, text="Recovered")

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        executor = HttpExecutor(FrameworkConfig(retries=2, retry_delay=0.01))
        req = HttpRequestModel(url="https://api.test/retry")
        resp = await executor.execute_request(req, client=client)
        assert resp.status_code == 200
        assert resp.text == "Recovered"
        assert attempts == 3


@pytest.mark.asyncio
async def test_executor_max_retries_exceeded() -> None:
    """Verify HttpRequestError is raised when retries are exhausted."""

    def mock_fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timeout")

    transport = httpx.MockTransport(mock_fail)
    async with httpx.AsyncClient(transport=transport) as client:
        executor = HttpExecutor(FrameworkConfig(retries=1, retry_delay=0.01))
        req = HttpRequestModel(url="https://api.test/fail")
        with pytest.raises(HttpRequestError, match="failed after 2 attempts"):
            await executor.execute_request(req, client=client)


@pytest.mark.asyncio
async def test_suite_chaining_and_hooks() -> None:
    """Verify SuiteExecutor executes setup/teardown hooks and chains extracted variables."""
    state: dict[str, Any] = {"setup_called": False, "teardown_called": False}

    def mock_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/setup":
            state["setup_called"] = True
            return httpx.Response(200, json={"status": "ready"})
        if request.url.path == "/teardown":
            state["teardown_called"] = True
            return httpx.Response(200, json={"status": "cleaned"})
        if request.method == "POST" and request.url.path == "/items":
            return httpx.Response(201, json={"item_id": "ITEM-999"})
        if request.method == "GET" and request.url.path == "/items/ITEM-999":
            return httpx.Response(200, json={"id": "ITEM-999", "status": "active"})
        return httpx.Response(404)

    transport = httpx.MockTransport(mock_handler)

    suite = TestSuiteModel(
        name="Chaining Suite",
        base_url="https://api.test",
        hooks=HookModel(
            setup=[HttpRequestModel(url="/setup")],
            teardown=[HttpRequestModel(url="/teardown")],
        ),
        tests=[
            # Step 1: Create item and extract item_id
            TestCaseModel(
                name="Create Item",
                request=HttpRequestModel(method="POST", url="/items", json={"name": "Widget"}),
                assertions=AssertionModel(status_code=201),
                extract=[
                    VariableExtractionModel(
                        name="created_id",
                        source="jsonpath",
                        expression="$.item_id",
                    )
                ],
            ),
            # Step 2: Use extracted variable in URL
            TestCaseModel(
                name="Get Item",
                request=HttpRequestModel(method="GET", url="/items/{{ created_id }}"),
                assertions=AssertionModel(
                    status_code=200,
                    jsonpath=[
                        JsonPathAssertionModel(path="$.status", op="equals", expected="active")
                    ],
                ),
            ),
        ],
    )

    executor = SuiteExecutor(FrameworkConfig())
    # Override client in HttpExecutor for testing
    orig_exec = executor.executor.execute_request

    async def mock_exec(request: HttpRequestModel, **kwargs: Any) -> Any:
        async with httpx.AsyncClient(transport=transport) as cl:
            kwargs["client"] = cl
            return await orig_exec(request=request, **kwargs)

    executor.executor.execute_request = mock_exec  # type: ignore[assignment]

    result = await executor.run_suite_async(suite)
    assert result.passed is True
    assert result.total_cases == 2
    assert result.passed_cases == 2
    assert state["setup_called"] is True
    assert state["teardown_called"] is True


def test_suite_case_skipped() -> None:
    """Verify skipped test cases are recorded as skipped."""
    suite = TestSuiteModel(
        name="Skip Suite",
        base_url="https://api.test",
        tests=[
            TestCaseModel(
                name="Skipped Case",
                skip="Skipped for test",
                request=HttpRequestModel(url="/ping"),
            )
        ],
    )
    executor = SuiteExecutor()
    result = executor.run_suite(suite)
    assert result.total_cases == 1
    assert result.skipped_cases == 1
    assert result.passed is True
    assert result.case_results[0].skipped is True
    assert result.case_results[0].skip_reason == "Skipped for test"


@pytest.mark.asyncio
async def test_parallel_executor() -> None:
    """Verify ParallelExecutor executes multiple suites concurrently."""

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(mock_handler)

    suite1 = TestSuiteModel(
        name="Suite 1",
        tests=[TestCaseModel(name="Case 1", request=HttpRequestModel(url="https://api.test/1"))],
    )
    suite2 = TestSuiteModel(
        name="Suite 2",
        tests=[TestCaseModel(name="Case 2", request=HttpRequestModel(url="https://api.test/2"))],
    )

    parallel = ParallelExecutor(max_workers=2)

    # Monkeypatch transport in HttpExecutor
    orig_exec = HttpExecutor.execute_request

    async def mock_exec(self: HttpExecutor, request: HttpRequestModel, **kwargs: Any) -> Any:
        async with httpx.AsyncClient(transport=transport) as cl:
            kwargs["client"] = cl
            return await orig_exec(self, request=request, **kwargs)

    HttpExecutor.execute_request = mock_exec  # type: ignore[assignment]

    results = await parallel.run_suites_async([suite1, suite2])
    assert len(results) == 2
    assert results[0].passed is True
    assert results[1].passed is True


def test_executor_execute_request_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify synchronous execution path in HttpExecutor."""

    def mock_request(self: httpx.Client, method: str, url: str, **kwargs: Any) -> httpx.Response:
        return httpx.Response(
            200,
            json={"sync": True},
            headers={"x-test": "sync"},
            request=httpx.Request(method, url),
        )

    monkeypatch.setattr(httpx.Client, "request", mock_request)

    executor = HttpExecutor(FrameworkConfig(base_url="https://api.test"))
    req = HttpRequestModel(method="GET", url="/sync-test")
    resp = executor.execute_request_sync(req)
    assert resp.status_code == 200
    assert resp.body == {"sync": True}
    assert resp.headers["x-test"] == "sync"


def test_executor_execute_request_sync_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify synchronous execution raises HttpRequestError on failure."""

    def mock_fail(self: httpx.Client, method: str, url: str, **kwargs: Any) -> httpx.Response:
        raise httpx.ConnectError("Network down")

    monkeypatch.setattr(httpx.Client, "request", mock_fail)

    executor = HttpExecutor(FrameworkConfig(retries=1, retry_delay=0.01))
    req = HttpRequestModel(method="GET", url="https://api.test/sync-fail")
    with pytest.raises(HttpRequestError, match="failed after 2 attempts"):
        executor.execute_request_sync(req)
