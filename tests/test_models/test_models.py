"""Tests for test definition and execution models."""

from __future__ import annotations

from api_test_framework.models.assertion import (
    AssertionModel,
    HeaderAssertionModel,
    JsonPathAssertionModel,
)
from api_test_framework.models.request import (
    AuthModel,
    HttpRequestModel,
)
from api_test_framework.models.response import HttpResponseData
from api_test_framework.models.result import (
    AssertionResult,
    TestCaseResult,
    TestSuiteResult,
)
from api_test_framework.models.test_case import (
    TestCaseModel,
)
from api_test_framework.models.test_suite import TestSuiteModel


def test_http_request_model_defaults() -> None:
    """Verify default values and alias handling in HttpRequestModel."""
    req = HttpRequestModel(url="/test")
    assert req.method == "GET"
    assert req.url == "/test"
    assert req.headers == {}
    assert req.query_params == {}
    assert req.path_params == {}
    assert req.json_body is None

    # Alias check for 'json'
    req_json = HttpRequestModel(url="/test", json={"a": 1})
    assert req_json.json_body == {"a": 1}


def test_auth_model_types() -> None:
    """Verify AuthModel validation across different auth strategies."""
    bearer = AuthModel(type="bearer", token="tok123")
    assert bearer.type == "bearer"
    assert bearer.token == "tok123"

    basic = AuthModel(type="basic", username="u", password="p")
    assert basic.username == "u"
    assert basic.password == "p"

    api_key = AuthModel(type="api_key", key_name="X-Key", key_value="val", location="query")
    assert api_key.location == "query"

    oauth2 = AuthModel(
        type="oauth2",
        token_url="https://auth.example.com",
        client_id="cid",
        client_secret="sec",
    )
    assert oauth2.client_id == "cid"


def test_assertion_model_structures() -> None:
    """Verify structure and alias handling of AssertionModel."""
    model = AssertionModel(
        status_code=200,
        headers={"content-type": "application/json"},
        schema={"type": "object"},
        max_duration=1.5,
    )
    assert model.status_code == 200
    assert model.schema_def == {"type": "object"}
    assert model.max_duration == 1.5

    jsonpath_rule = JsonPathAssertionModel(path="$.id", op="equals", expected=1)
    header_rule = HeaderAssertionModel(name="X-Trace", op="exists")
    assert jsonpath_rule.op == "equals"
    assert header_rule.op == "exists"


def test_test_case_model_validation() -> None:
    """Verify TestCaseModel attributes, tags, and delays."""
    req = HttpRequestModel(url="/status")
    case = TestCaseModel(
        name="Status Check",
        description="Verify service health",
        tags=["health", "critical"],
        request=req,
        retries=2,
        delay_before=0.1,
        skip="Feature disabled",
    )
    assert case.name == "Status Check"
    assert "health" in case.tags
    assert case.retries == 2
    assert case.skip == "Feature disabled"


def test_test_suite_model_aliases() -> None:
    """Verify TestSuiteModel parses both 'test_cases' and 'tests' alias."""
    data = {
        "name": "Suite A",
        "tests": [
            {
                "name": "Case 1",
                "request": {"url": "/ping"},
            }
        ],
    }
    suite = TestSuiteModel.model_validate(data)
    assert suite.name == "Suite A"
    assert len(suite.test_cases) == 1
    assert suite.test_cases[0].name == "Case 1"


def test_result_models() -> None:
    """Verify AssertionResult, TestCaseResult, and TestSuiteResult behavior."""
    assert_res = AssertionResult(
        name="status_check",
        passed=True,
        expected=200,
        actual=200,
        message="OK",
    )
    assert assert_res.passed is True

    resp = HttpResponseData(
        status_code=200,
        headers={},
        body=None,
        text="OK",
        elapsed_seconds=0.05,
        url="https://api.example.com",
    )

    case_res = TestCaseResult(
        case_name="Test 1",
        suite_name="Suite 1",
        passed=True,
        duration_seconds=0.05,
        assertion_results=[assert_res],
        response=resp,
    )
    assert case_res.passed is True

    suite_res = TestSuiteResult(
        suite_name="Suite 1",
        case_results=[case_res],
        duration_seconds=0.05,
        passed=True,
        total_cases=1,
        passed_cases=1,
        failed_cases=0,
        skipped_cases=0,
    )
    assert suite_res.total_cases == 1
    assert suite_res.passed is True
