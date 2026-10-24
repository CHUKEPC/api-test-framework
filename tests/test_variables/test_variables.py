"""Tests for variable management, templating, and response extraction."""

from __future__ import annotations

import pytest

from api_test_framework.exceptions import VariableError, VariableExtractionError
from api_test_framework.models.response import HttpResponseData
from api_test_framework.variables import VariableManager


def test_variable_manager_set_get() -> None:
    """Verify storing and retrieving variables."""
    vm = VariableManager({"initial": "alpha"})
    assert vm.get("initial") == "alpha"
    assert vm.get("missing", default="beta") == "beta"

    vm.set("gamma", 123)
    assert vm.get("gamma") == 123


def test_variable_manager_env_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify fallback to os.environ when variable is not in local store."""
    monkeypatch.setenv("TEST_GLOBAL_VAR", "system_val")
    vm = VariableManager()
    assert vm.get("TEST_GLOBAL_VAR") == "system_val"


def test_variable_manager_shell_style_substitution(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify ${VAR} and ${VAR:-default} syntax substitution."""
    monkeypatch.setenv("MY_ENV", "prod")
    vm = VariableManager({"local_var": "local"})

    res1 = vm.render("https://${MY_ENV}.example.com")
    assert res1 == "https://prod.example.com"

    res2 = vm.render("${NONEXISTENT:-fallback}")
    assert res2 == "fallback"


def test_variable_manager_jinja2_rendering() -> None:
    """Verify Jinja2 template rendering."""
    vm = VariableManager({"name": "world", "count": 42})
    assert vm.render("Hello, {{ name }}!") == "Hello, world!"
    # Verify native type preservation
    assert vm.render("{{ count }}") == 42


def test_variable_manager_custom_functions() -> None:
    """Verify built-in helper functions in Jinja templates."""
    vm = VariableManager()
    rendered_uuid = vm.render("{{ uuid() }}")
    assert isinstance(rendered_uuid, str)
    assert len(rendered_uuid) == 36

    rendered_ts = vm.render("{{ timestamp() }}")
    assert isinstance(rendered_ts, int)

    rendered_int = vm.render("{{ random_int(10, 20) }}")
    assert 10 <= rendered_int <= 20

    rendered_str = vm.render("{{ random_str(12) }}")
    assert len(rendered_str) == 12

    rendered_iso = vm.render("{{ now_iso() }}")
    assert "T" in rendered_iso


def test_variable_manager_recursive_rendering() -> None:
    """Verify recursive rendering of dictionaries and lists."""
    vm = VariableManager({"base": "api", "id": 99})
    data = {
        "url": "/{{ base }}/items",
        "nested": {
            "item_id": "{{ id }}",
        },
        "tags": ["tag-{{ id }}", 100],
    }
    rendered = vm.render(data)
    assert rendered["url"] == "/api/items"
    assert rendered["nested"]["item_id"] == 99
    assert rendered["tags"] == ["tag-99", 100]


def test_variable_manager_invalid_template() -> None:
    """Verify VariableError when rendering syntax is broken."""
    vm = VariableManager()
    with pytest.raises(VariableError, match="Failed to render"):
        vm.render("{{ broken syntax %}")


def test_variable_extraction_jsonpath(sample_response_data: HttpResponseData) -> None:
    """Verify extraction using JSONPath."""
    vm = VariableManager()
    val = vm.extract("jsonpath", "$.name", sample_response_data)
    assert val == "Antigravity"

    role = vm.extract("jsonpath", "$.roles[0]", sample_response_data)
    assert role == "admin"


def test_variable_extraction_header(sample_response_data: HttpResponseData) -> None:
    """Verify extraction from response headers."""
    vm = VariableManager()
    val = vm.extract("header", "content-type", sample_response_data)
    assert val == "application/json"


def test_variable_extraction_regex(sample_response_data: HttpResponseData) -> None:
    """Verify extraction using regex with capturing group."""
    vm = VariableManager()
    val = vm.extract("regex", r'"city":\s*"([^"]+)"', sample_response_data)
    assert val == "London"


def test_variable_extraction_edge_cases() -> None:
    """Verify extraction error branches and fallbacks."""
    vm = VariableManager()
    empty_resp = HttpResponseData(
        status_code=204,
        headers={},
        body=None,
        text="",
        url="https://api.test",
    )
    with pytest.raises(VariableExtractionError, match="Response body is empty"):
        vm.extract("jsonpath", "$.id", empty_resp)

    assert vm.extract("jsonpath", "$.id", empty_resp, default=42) == 42
    assert vm.extract("header", "missing-hdr", empty_resp, default="hdr-def") == "hdr-def"
    with pytest.raises(VariableExtractionError, match="Header 'x-missing' not found"):
        vm.extract("header", "x-missing", empty_resp)

    assert vm.extract("regex", r"abc", empty_resp, default="re-def") == "re-def"
    with pytest.raises(VariableExtractionError, match="Regex 'xyz' did not match"):
        vm.extract("regex", r"xyz", empty_resp)

    # Whole body extraction
    assert vm.extract("body", "", empty_resp) == ""
    with pytest.raises(VariableExtractionError, match="Unsupported extraction source"):
        vm.extract("unknown_src", "", empty_resp)


def test_variable_extraction_failure_and_default(sample_response_data: HttpResponseData) -> None:
    """Verify extraction error when missing vs returning default value."""
    vm = VariableManager()
    with pytest.raises(VariableExtractionError, match="found no matches"):
        vm.extract("jsonpath", "$.nonexistent", sample_response_data)

    fallback = vm.extract("jsonpath", "$.nonexistent", sample_response_data, default="default_val")
    assert fallback == "default_val"
