"""Tests for test suite loading and schema validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from api_test_framework.exceptions import DSLValidationError
from api_test_framework.loader import (
    load_test_suite,
    load_test_suite_from_json,
    load_test_suite_from_yaml,
    validate_test_suite_dict,
)


def test_validate_test_suite_dict_valid() -> None:
    """Verify validation succeeds for a valid dictionary."""
    data = {
        "name": "Sample Suite",
        "tests": [
            {
                "name": "Ping test",
                "request": {"url": "/ping", "method": "GET"},
            }
        ],
    }
    suite = validate_test_suite_dict(data)
    assert suite.name == "Sample Suite"
    assert len(suite.test_cases) == 1


def test_validate_test_suite_dict_invalid_root() -> None:
    """Verify DSLValidationError is raised when input is not a mapping."""
    with pytest.raises(
        DSLValidationError, match="Expected root of test definition to be a mapping"
    ):
        validate_test_suite_dict(["not", "a", "dict"])


def test_validate_test_suite_dict_missing_required() -> None:
    """Verify DSLValidationError is raised when required fields are missing."""
    with pytest.raises(DSLValidationError, match="DSL schema validation failed"):
        validate_test_suite_dict({"description": "Missing name and tests"})


def test_load_yaml_from_string() -> None:
    """Verify loading test suite from raw YAML text."""
    yaml_content = """
name: "YAML String Suite"
base_url: "https://example.com"
tests:
  - name: "Case 1"
    request:
      url: "/endpoint"
"""
    suite = load_test_suite_from_yaml(yaml_content)
    assert suite.name == "YAML String Suite"
    assert suite.base_url == "https://example.com"


def test_load_yaml_from_file(tmp_path: Path) -> None:
    """Verify loading test suite from a YAML file."""
    file_path = tmp_path / "test_api.yaml"
    data = {
        "name": "File Suite",
        "tests": [{"name": "File Case", "request": {"url": "/file"}}],
    }
    file_path.write_text(yaml.dump(data), encoding="utf-8")

    suite = load_test_suite_from_yaml(file_path)
    assert suite.name == "File Suite"


def test_load_yaml_file_not_found(tmp_path: Path) -> None:
    """Verify error when YAML file does not exist."""
    missing = tmp_path / "nonexistent.yaml"
    with pytest.raises(DSLValidationError, match="not found"):
        load_test_suite_from_yaml(missing)


def test_load_yaml_invalid_syntax(tmp_path: Path) -> None:
    """Verify error on invalid YAML syntax."""
    file_path = tmp_path / "broken.yaml"
    file_path.write_text("name: broken: syntax : [", encoding="utf-8")
    with pytest.raises(DSLValidationError, match="Invalid YAML syntax"):
        load_test_suite_from_yaml(file_path)


def test_load_yaml_empty(tmp_path: Path) -> None:
    """Verify error on empty YAML file."""
    file_path = tmp_path / "empty.yaml"
    file_path.write_text("", encoding="utf-8")
    with pytest.raises(DSLValidationError, match="empty"):
        load_test_suite_from_yaml(file_path)


def test_load_json_from_file(tmp_path: Path) -> None:
    """Verify loading test suite from a JSON file."""
    file_path = tmp_path / "test_suite.json"
    data = {
        "name": "JSON Suite",
        "tests": [{"name": "JSON Case", "request": {"url": "/json"}}],
    }
    file_path.write_text(json.dumps(data), encoding="utf-8")

    suite = load_test_suite_from_json(file_path)
    assert suite.name == "JSON Suite"


def test_load_json_invalid_syntax(tmp_path: Path) -> None:
    """Verify error on invalid JSON syntax."""
    file_path = tmp_path / "broken.json"
    file_path.write_text("{broken json", encoding="utf-8")
    with pytest.raises(DSLValidationError, match="Invalid JSON syntax"):
        load_test_suite_from_json(file_path)


def test_load_test_suite_auto_detect(tmp_path: Path) -> None:
    """Verify load_test_suite detects .yaml vs .json extension."""
    y_file = tmp_path / "test_a.yaml"
    y_file.write_text("name: 'A'\ntests: [{name: 't', request: {url: '/'}}]", encoding="utf-8")

    j_file = tmp_path / "test_b.json"
    j_file.write_text(
        '{"name": "B", "tests": [{"name": "t", "request": {"url": "/"}}]}', encoding="utf-8"
    )

    suite_y = load_test_suite(y_file)
    suite_j = load_test_suite(j_file)

    assert suite_y.name == "A"
    assert suite_j.name == "B"
