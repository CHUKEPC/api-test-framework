"""Tests for all assertion engine components."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from api_test_framework.assertions import (
    assert_body_contains,
    assert_body_deep,
    assert_body_exact,
    assert_body_regex,
    assert_headers,
    assert_json_schema,
    assert_jsonpath,
    assert_max_duration,
    assert_status_code,
    clear_custom_assertions,
    evaluate_assertions,
    register_custom_assertion,
)
from api_test_framework.models.assertion import (
    AssertionModel,
    HeaderAssertionModel,
    JsonPathAssertionModel,
)
from api_test_framework.models.response import HttpResponseData
from api_test_framework.models.result import AssertionResult
from api_test_framework.variables import VariableManager


def test_assert_status_code() -> None:
    """Verify status code checking for single code and lists."""
    res1 = assert_status_code(200, 200)
    assert res1.passed is True

    res2 = assert_status_code(200, 404)
    assert res2.passed is False

    res3 = assert_status_code([200, 201, 204], 201)
    assert res3.passed is True

    res4 = assert_status_code([200, 201], 500)
    assert res4.passed is False


def test_assert_headers() -> None:
    """Verify header assertions including case-insensitivity and operators."""
    headers = {"Content-Type": "application/json; charset=utf-8", "X-Request-Id": "req-123"}

    # Equals
    r1 = assert_headers({"x-request-id": "req-123"}, headers)
    assert r1[0].passed is True

    # Contains
    r2 = assert_headers(
        {"content-type": {"op": "contains", "expected": "application/json"}}, headers
    )
    assert r2[0].passed is True

    # Regex
    r3 = assert_headers({"x-request-id": {"op": "regex", "expected": r"req-\d+"}}, headers)
    assert r3[0].passed is True

    # Exists
    r4 = assert_headers([HeaderAssertionModel(name="x-request-id", op="exists")], headers)
    assert r4[0].passed is True

    # Missing header
    r5 = assert_headers({"authorization": "Bearer xyz"}, headers)
    assert r5[0].passed is False


def test_assert_body_exact_contains_regex() -> None:
    """Verify exact match, substring containment, and regex checks on body."""
    text = "User created successfully with ID: 4567"
    assert assert_body_exact(text, text).passed is True
    assert assert_body_exact("Different", text).passed is False

    assert assert_body_contains("ID: 4567", text).passed is True
    assert assert_body_contains("ID: 9999", text).passed is False

    assert assert_body_regex(r"ID:\s*\d+", text).passed is True
    assert assert_body_regex(r"^Failed", text).passed is False


def test_assert_body_deep_comparison() -> None:
    """Verify deep dictionary and list comparison."""
    actual = {
        "status": "ok",
        "data": {
            "id": 1,
            "tags": ["alpha", "beta"],
        },
    }

    # Matching subset
    res_pass = assert_body_deep({"data": {"id": 1}}, actual)
    assert all(r.passed for r in res_pass)

    # Missing key
    res_missing = assert_body_deep({"data": {"missing_key": True}}, actual)
    assert any(not r.passed for r in res_missing)

    # List mismatch
    res_list = assert_body_deep({"data": {"tags": ["alpha", "wrong"]}}, actual)
    assert any(not r.passed for r in res_list)


def test_assert_jsonpath_operators() -> None:
    """Verify JSONPath assertion operators."""
    body = {
        "items": [
            {"id": 1, "price": 10.5, "title": "Book"},
            {"id": 2, "price": 25.0, "title": "Pen"},
        ],
        "total": 2,
        "active": True,
    }

    # equals & not_equals
    assert assert_jsonpath({"$.total": 2}, body)[0].passed is True
    assert (
        assert_jsonpath(
            [JsonPathAssertionModel(path="$.total", op="not_equals", expected=5)], body
        )[0].passed
        is True
    )

    # contains
    assert (
        assert_jsonpath(
            [JsonPathAssertionModel(path="$.items[0].title", op="contains", expected="oo")], body
        )[0].passed
        is True
    )

    # numeric comparisons: gt, gte, lt, lte
    assert (
        assert_jsonpath(
            [JsonPathAssertionModel(path="$.items[1].price", op="gt", expected=20.0)], body
        )[0].passed
        is True
    )
    assert (
        assert_jsonpath(
            [JsonPathAssertionModel(path="$.items[1].price", op="lte", expected=25.0)], body
        )[0].passed
        is True
    )

    # type
    assert (
        assert_jsonpath(
            [JsonPathAssertionModel(path="$.active", op="type", expected="bool")], body
        )[0].passed
        is True
    )

    # len
    assert (
        assert_jsonpath([JsonPathAssertionModel(path="$.items", op="len", expected=2)], body)[
            0
        ].passed
        is True
    )

    # regex
    assert (
        assert_jsonpath(
            [JsonPathAssertionModel(path="$.items[0].title", op="regex", expected=r"^B\w+k$")],
            body,
        )[0].passed
        is True
    )

    # exists
    assert (
        assert_jsonpath([JsonPathAssertionModel(path="$.items[0].id", op="exists")], body)[
            0
        ].passed
        is True
    )
    assert (
        assert_jsonpath(
            [JsonPathAssertionModel(path="$.missing", op="exists", expected=False)], body
        )[0].passed
        is True
    )


def test_assert_json_schema(tmp_path: Path) -> None:
    """Verify JSON Schema validation from dict and file."""
    schema = {
        "type": "object",
        "required": ["id", "name"],
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
        },
    }

    valid_payload = {"id": 10, "name": "Test"}
    invalid_payload = {"id": "not-an-int", "name": "Test"}

    assert assert_json_schema(schema, valid_payload).passed is True
    assert assert_json_schema(schema, invalid_payload).passed is False

    # From JSON file
    schema_file = tmp_path / "schema.json"
    schema_file.write_text(json.dumps(schema), encoding="utf-8")
    assert assert_json_schema(str(schema_file), valid_payload).passed is True

    # From YAML file
    yaml_schema_file = tmp_path / "schema.yaml"
    yaml_schema_file.write_text(yaml.dump(schema), encoding="utf-8")
    assert assert_json_schema(str(yaml_schema_file), valid_payload).passed is True


def test_assert_max_duration() -> None:
    """Verify response duration assertions."""
    assert assert_max_duration(1.0, 0.45).passed is True
    assert assert_max_duration(0.5, 1.20).passed is False


def test_custom_assertion_registry(sample_response_data: HttpResponseData) -> None:
    """Verify registering and invoking custom assertion functions."""
    clear_custom_assertions()

    def check_is_antigravity(resp: HttpResponseData) -> AssertionResult:
        is_anti = resp.body.get("name") == "Antigravity"
        return AssertionResult(
            name="custom:check_is_antigravity",
            passed=is_anti,
            expected="Antigravity",
            actual=resp.body.get("name"),
            message="Checked Antigravity",
        )

    register_custom_assertion("check_is_antigravity", check_is_antigravity)

    assertions = AssertionModel(custom=["check_is_antigravity", "unregistered_check"])
    results = evaluate_assertions(assertions, sample_response_data)
    assert len(results) == 2
    assert results[0].passed is True
    assert results[1].passed is False
    assert "not registered" in results[1].message


def test_evaluate_assertions_comprehensive(sample_response_data: HttpResponseData) -> None:
    """Verify evaluate_assertions combining all check types with variable rendering."""
    vm = VariableManager({"expected_city": "London", "max_time": 2.0})

    assertions = AssertionModel(
        status_code=200,
        headers={"content-type": "application/json"},
        body={"name": "Antigravity"},
        body_contains="active",
        body_regex=r'"age":\s*\d+',
        jsonpath={"$.profile.city": "{{ expected_city }}"},
        max_duration=2.0,
    )

    results = evaluate_assertions(assertions, sample_response_data, vm)
    assert all(r.passed for r in results)
