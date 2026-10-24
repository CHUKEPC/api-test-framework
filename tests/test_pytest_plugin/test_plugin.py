"""Tests for pytest integration, YAML test discovery, and fixtures."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from api_test_framework.models.assertion import AssertionModel
from api_test_framework.models.request import HttpRequestModel
from api_test_framework.models.test_case import TestCaseModel, VariableExtractionModel
from api_test_framework.models.test_suite import TestSuiteModel
from api_test_framework.pytest_plugin import (
    YamlFile,
    YamlItem,
    api_client,
    api_vars,
    auth_token,
    base_url,
    pytest_addoption,
    pytest_collect_file,
    pytest_configure,
)
from api_test_framework.runner.executor import HttpExecutor
from api_test_framework.variables import VariableManager


def test_pytest_addoption_and_configure() -> None:
    """Verify registration of CLI options and markers."""
    parser = MagicMock()
    group = MagicMock()
    parser.getgroup.return_value = group

    pytest_addoption(parser)
    assert group.addoption.call_count >= 5

    config = MagicMock()
    pytest_configure(config)
    config.addinivalue_line.assert_called_once_with(
        "markers", "api_test: mark test as a declarative REST API test"
    )


def test_pytest_collect_file(tmp_path: Path) -> None:
    """Verify pytest_collect_file collects YAML test files and ignores others."""
    parent = MagicMock()

    # Valid test YAML file
    yaml_file = tmp_path / "test_users.yaml"
    yaml_file.write_text(
        "name: 'Users'\ntests: [{name: 'Get Users', request: {url: '/users'}}]", encoding="utf-8"
    )

    collector = pytest_collect_file(yaml_file, parent)
    assert collector is not None
    assert isinstance(collector, YamlFile)

    # Non-test YAML file
    config_yaml = tmp_path / "config.yaml"
    config_yaml.write_text("env: prod", encoding="utf-8")
    assert pytest_collect_file(config_yaml, parent) is None

    # Python file
    py_file = tmp_path / "test_sample.py"
    py_file.write_text("def test_x(): pass", encoding="utf-8")
    assert pytest_collect_file(py_file, parent) is None


def test_yaml_item_runtest_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify YamlItem executes test case, validates assertions, and extracts variables."""

    def mock_sync_request(
        self: HttpExecutor, request: HttpRequestModel, **kwargs: object
    ) -> object:
        from api_test_framework.models.response import HttpResponseData

        return HttpResponseData(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body={"id": 888, "status": "ok"},
            text='{"id": 888, "status": "ok"}',
            elapsed_seconds=0.1,
            url="https://api.test/resource",
        )

    monkeypatch.setattr(HttpExecutor, "execute_request_sync", mock_sync_request)

    case = TestCaseModel(
        name="Fetch Resource",
        tags=["smoke"],
        request=HttpRequestModel(url="/resource"),
        assertions=AssertionModel(status_code=200),
        extract=[
            VariableExtractionModel(name="extracted_id", source="jsonpath", expression="$.id")
        ],
    )
    suite = TestSuiteModel(name="Sample Suite", base_url="https://api.test", tests=[case])

    parent = MagicMock()
    parent.path = tmp_path / "test_resource.yaml"

    vm = VariableManager()
    cfg = MagicMock()
    cfg.base_url = "https://api.test"

    item = YamlItem.from_parent(
        parent,
        name=case.name,
        case=case,
        suite=suite,
        variable_manager=vm,
        config_override=cfg,
    )

    # Run test
    item.runtest()
    assert vm.get("extracted_id") == 888

    # Check reportinfo
    _path, _line, desc = item.reportinfo()
    assert desc == "Sample Suite::Fetch Resource"


def test_yaml_item_runtest_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify YamlItem calls pytest.fail when assertions fail."""

    def mock_sync_request(
        self: HttpExecutor, request: HttpRequestModel, **kwargs: object
    ) -> object:
        from api_test_framework.models.response import HttpResponseData

        return HttpResponseData(
            status_code=500,
            headers={},
            body={"error": "Internal Error"},
            text='{"error": "Internal Error"}',
            elapsed_seconds=0.1,
            url="https://api.test/fail",
        )

    monkeypatch.setattr(HttpExecutor, "execute_request_sync", mock_sync_request)

    case = TestCaseModel(
        name="Failing Case",
        request=HttpRequestModel(url="/fail"),
        assertions=AssertionModel(status_code=200),
    )
    suite = TestSuiteModel(name="Suite", tests=[case])

    parent = MagicMock()
    parent.path = tmp_path / "test_fail.yaml"
    item = YamlItem.from_parent(
        parent,
        name=case.name,
        case=case,
        suite=suite,
        variable_manager=VariableManager(),
        config_override=MagicMock(),
    )

    with pytest.raises(pytest.fail.Exception, match="Failed 1 assertion"):
        item.runtest()


def test_fixture_logic() -> None:
    """Verify fixture helper functions configure instances."""
    req_mock = MagicMock()
    req_mock.config.getoption.side_effect = lambda opt, default=None: (
        "https://cli-base.test" if opt == "--api-base-url" else "cli-token-xyz"
    )

    url = base_url.__wrapped__(req_mock)
    assert url == "https://cli-base.test"

    token = auth_token.__wrapped__(req_mock)
    assert token == "cli-token-xyz"

    client = api_client.__wrapped__(url, token)
    assert isinstance(client, HttpExecutor)
    assert client.config.base_url == "https://cli-base.test"
    assert client.config.auth_token == "cli-token-xyz"

    vm = api_vars.__wrapped__()
    assert isinstance(vm, VariableManager)
