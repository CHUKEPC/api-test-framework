"""Pytest plugin providing YAML test collection, API fixtures, and CLI options."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from api_test_framework.assertions import evaluate_assertions
from api_test_framework.config import FrameworkConfig
from api_test_framework.loader.yaml_loader import load_test_suite_from_yaml
from api_test_framework.runner.chain import SuiteExecutor
from api_test_framework.runner.executor import HttpExecutor
from api_test_framework.variables import VariableManager

if TYPE_CHECKING:
    from collections.abc import Generator

    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from _pytest.nodes import Item

    from api_test_framework.models.test_case import TestCaseModel
    from api_test_framework.models.test_suite import TestSuiteModel


def pytest_addoption(parser: Parser) -> None:
    """Register custom CLI options for api-test-framework in pytest."""
    group = parser.getgroup("api-test-framework", "REST API testing options")
    group.addoption(
        "--api-base-url",
        action="store",
        default=None,
        help="Base URL override for REST API test requests.",
    )
    group.addoption(
        "--api-auth-token",
        action="store",
        default=None,
        help="Authorization token override for API requests.",
    )
    group.addoption(
        "--api-env",
        action="store",
        default=None,
        help="Path to environment variables file.",
    )
    group.addoption(
        "--api-timeout",
        action="store",
        type=float,
        default=None,
        help="Default timeout in seconds for API requests.",
    )
    group.addoption(
        "--api-report-html",
        action="store",
        default=None,
        help="File path to save generated HTML report.",
    )
    group.addoption(
        "--api-report-json",
        action="store",
        default=None,
        help="File path to save generated JSON report.",
    )


def pytest_configure(config: Config) -> None:
    """Register custom markers for API tests."""
    config.addinivalue_line(
        "markers",
        "api_test: mark test as a declarative REST API test",
    )


def pytest_collect_file(
    file_path: Path,
    parent: pytest.Collector,
) -> pytest.Collector | None:
    """Collect YAML files containing declarative API test suites."""
    name = file_path.name.lower()
    if name.endswith((".yaml", ".yml")) and (
        name.startswith("test_") or name.endswith(("_test.yaml", "_test.yml"))
    ):
        try:
            # Check if it looks like an api-test-framework test suite
            suite = load_test_suite_from_yaml(file_path)
            if suite and suite.test_cases:
                return YamlFile.from_parent(parent, path=file_path)
        except Exception:
            return None
    return None


class YamlFile(pytest.File):
    """Collector representing a YAML file containing a test suite."""

    def collect(self) -> Generator[Item, None, None]:
        """Parse YAML suite and yield YamlItem for each contained test case."""
        suite = load_test_suite_from_yaml(self.path)
        base_vars = dict(suite.variables)
        variable_manager = VariableManager(base_vars)

        config_override = self._get_config_override()

        for case in suite.test_cases:
            yield YamlItem.from_parent(
                self,
                name=case.name,
                case=case,
                suite=suite,
                variable_manager=variable_manager,
                config_override=config_override,
            )

    def _get_config_override(self) -> FrameworkConfig:
        """Build FrameworkConfig from pytest command-line flags."""
        base_url = self.config.getoption("--api-base-url", default=None)
        token = self.config.getoption("--api-auth-token", default=None)
        timeout = self.config.getoption("--api-timeout", default=None)
        env_file = self.config.getoption("--api-env", default=None)

        cfg = FrameworkConfig.from_env(env_file)
        if base_url:
            cfg.base_url = base_url
        if token:
            cfg.auth_token = token
        if timeout is not None:
            cfg.timeout = timeout
        return cfg


class YamlItem(pytest.Item):
    """Executable pytest test item corresponding to a TestCaseModel."""

    def __init__(
        self,
        name: str,
        parent: YamlFile,
        case: TestCaseModel,
        suite: TestSuiteModel,
        variable_manager: VariableManager,
        config_override: FrameworkConfig,
    ) -> None:
        """Initialize YamlItem."""
        super().__init__(name, parent)
        self.case = case
        self.suite = suite
        self.variable_manager = variable_manager
        self.config_override = config_override

        # Register markers
        self.add_marker(pytest.mark.api_test)
        for tag in case.tags:
            self.add_marker(tag)

    def runtest(self) -> None:
        """Execute the test case and assert all expectations."""
        if self.case.skip:
            reason = (
                str(self.case.skip)
                if isinstance(self.case.skip, str)
                else "Skipped by YAML definition"
            )
            pytest.skip(reason)

        executor = SuiteExecutor(self.config_override)
        rendered_request = executor._render_request(self.case.request, self.variable_manager)

        effective_base_url = self.config_override.base_url or self.suite.base_url

        try:
            response = executor.executor.execute_request_sync(
                request=rendered_request,
                base_url=effective_base_url,
                retries=self.case.retries,
                retry_delay=self.case.retry_delay,
            )
        except Exception as exc:
            pytest.fail(f"Request failed: {exc}", pytrace=False)

        assertion_results = evaluate_assertions(
            self.case.assertions,
            response,
            self.variable_manager,
        )

        failed_asserts = [a for a in assertion_results if not a.passed]
        if failed_asserts:
            lines = [f"Failed {len(failed_asserts)} assertion(s):"]
            for a in failed_asserts:
                lines.append(f"  - [{a.assertion_type}] {a.name}: {a.message}")
            pytest.fail("\n".join(lines), pytrace=False)

        # Extract variables if passed
        for extraction in self.case.extract:
            val = self.variable_manager.extract(
                source=extraction.source,
                expression=extraction.expression,
                response=response,
                default=extraction.default,
            )
            self.variable_manager.set(extraction.name, val)

    def repr_failure(
        self,
        excinfo: pytest.ExceptionInfo[BaseException],
        style: Any = None,
    ) -> str:
        """Format failure representation for pytest console output."""
        if excinfo.errisinstance(pytest.fail.Exception):
            return str(excinfo.value)
        return str(super().repr_failure(excinfo))

    def reportinfo(self) -> tuple[Path, int, str]:
        """Return file path, line number, and test description for reporting."""
        return self.path, 0, f"{self.suite.name}::{self.name}"


# Pytest Fixtures


@pytest.fixture
def base_url(request: pytest.FixtureRequest) -> str | None:
    """Fixture returning configured API base URL from pytest CLI or environment."""
    cli_base_url = request.config.getoption("--api-base-url", default=None)
    if cli_base_url:
        return str(cli_base_url)
    cfg = FrameworkConfig.from_env()
    return cfg.base_url


@pytest.fixture
def auth_token(request: pytest.FixtureRequest) -> str | None:
    """Fixture returning configured API auth token from CLI or environment."""
    cli_token = request.config.getoption("--api-auth-token", default=None)
    if cli_token:
        return str(cli_token)
    cfg = FrameworkConfig.from_env()
    return cfg.auth_token


@pytest.fixture
def api_client(base_url: str | None, auth_token: str | None) -> HttpExecutor:
    """Fixture providing a configured HttpExecutor client instance."""
    cfg = FrameworkConfig(base_url=base_url, auth_token=auth_token)
    return HttpExecutor(cfg)


@pytest.fixture
def api_vars() -> VariableManager:
    """Fixture providing a fresh VariableManager context."""
    return VariableManager()
