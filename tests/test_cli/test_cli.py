"""Tests for Click command-line interface."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from api_test_framework.cli.app import cli
from api_test_framework.runner.executor import HttpExecutor


def test_cli_help() -> None:
    """Verify CLI help message and subcommands."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "REST API Testing Framework CLI" in result.output
    assert "run" in result.output
    assert "validate" in result.output
    assert "init" in result.output


def test_cli_init_command(tmp_path: Path) -> None:
    """Verify init command scaffolds new test suite YAML file."""
    runner = CliRunner()
    target_file = tmp_path / "starter_test.yaml"

    result = runner.invoke(cli, ["init", str(target_file)])
    assert result.exit_code == 0
    assert target_file.exists()
    assert "API Test Suite Specification" in target_file.read_text(encoding="utf-8")

    # Second invocation should warn and abort without overwriting
    result2 = runner.invoke(cli, ["init", str(target_file)])
    assert result2.exit_code == 1
    assert "already exists" in result2.output


def test_cli_validate_command_valid(tmp_path: Path) -> None:
    """Verify validate command succeeds for valid test file."""
    runner = CliRunner()
    file_path = tmp_path / "valid.yaml"
    file_path.write_text(
        "name: 'Validation Suite'\ntests: [{name: 'C1', request: {url: '/ping'}}]",
        encoding="utf-8",
    )

    result = runner.invoke(cli, ["validate", str(file_path)])
    assert result.exit_code == 0
    assert "Valid" in result.output


def test_cli_validate_command_invalid(tmp_path: Path) -> None:
    """Verify validate command fails and reports errors for invalid file."""
    runner = CliRunner()
    file_path = tmp_path / "invalid.yaml"
    file_path.write_text("broken: [syntax", encoding="utf-8")

    result = runner.invoke(cli, ["validate", str(file_path)])
    assert result.exit_code == 1
    assert "Invalid" in result.output or "Error" in result.output


def test_cli_run_command_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify run command executes tests and generates output reports."""

    async def mock_execute_request(
        self: HttpExecutor, request: object, **kwargs: object
    ) -> object:
        from api_test_framework.models.response import HttpResponseData

        return HttpResponseData(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body={"status": "alive"},
            text='{"status": "alive"}',
            elapsed_seconds=0.05,
            url="https://api.test/health",
        )

    monkeypatch.setattr(HttpExecutor, "execute_request", mock_execute_request)

    test_file = tmp_path / "test_health.yaml"
    test_file.write_text(
        """
name: 'Health Check Suite'
base_url: 'https://api.test'
tests:
  - name: 'Ping'
    request:
      url: '/health'
    assertions:
      status_code: 200
""",
        encoding="utf-8",
    )

    html_report = tmp_path / "report.html"
    junit_report = tmp_path / "report.xml"
    json_report = tmp_path / "report.json"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "run",
            str(test_file),
            "--report-html",
            str(html_report),
            "--report-junit",
            str(junit_report),
            "--report-json",
            str(json_report),
        ],
    )
    assert result.exit_code == 0
    assert "PASSED" in result.output
    assert html_report.exists()
    assert junit_report.exists()
    assert json_report.exists()


def test_cli_run_command_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify run command exits with code 1 when assertions fail."""

    def mock_request_sync(self: HttpExecutor, req: object, **kwargs: object) -> object:
        from api_test_framework.models.response import HttpResponseData

        return HttpResponseData(
            status_code=500,
            headers={},
            body=None,
            text="Server Error",
            elapsed_seconds=0.05,
            url="https://api.test/error",
        )

    monkeypatch.setattr(HttpExecutor, "execute_request_sync", mock_request_sync)

    test_file = tmp_path / "test_fail.yaml"
    test_file.write_text(
        """
name: 'Failing Suite'
tests:
  - name: 'Expect 200'
    request:
      url: 'https://api.test/error'
    assertions:
      status_code: 200
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["run", str(test_file)])
    assert result.exit_code == 1
    assert "FAILED" in result.output
