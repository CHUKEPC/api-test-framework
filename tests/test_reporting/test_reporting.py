"""Tests for Terminal, HTML, JUnit XML, and JSON test report generators."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET

from rich.console import Console

from api_test_framework.models.result import (
    AssertionResult,
    TestCaseResult,
    TestSuiteResult,
)
from api_test_framework.reporting.html import HtmlReporter
from api_test_framework.reporting.json_report import JsonReporter
from api_test_framework.reporting.junit import JunitReporter
from api_test_framework.reporting.terminal import TerminalReporter


def _create_mock_results() -> list[TestSuiteResult]:
    """Helper creating a mix of passed, failed, and skipped test results."""
    case_pass = TestCaseResult(
        case_name="Passing Test",
        suite_name="Auth Suite",
        passed=True,
        duration_seconds=0.12,
        assertion_results=[
            AssertionResult(name="status", passed=True, expected=200, actual=200, message="OK")
        ],
    )
    case_fail = TestCaseResult(
        case_name="Failing Test",
        suite_name="Auth Suite",
        passed=False,
        duration_seconds=0.08,
        assertion_results=[
            AssertionResult(
                name="status", passed=False, expected=200, actual=500, message="Server Error"
            )
        ],
    )
    case_skip = TestCaseResult(
        case_name="Skipped Test",
        suite_name="Auth Suite",
        passed=True,
        duration_seconds=0.0,
        skipped=True,
        skip_reason="WIP",
    )

    suite = TestSuiteResult(
        suite_name="Auth Suite",
        case_results=[case_pass, case_fail, case_skip],
        duration_seconds=0.20,
        passed=False,
        total_cases=3,
        passed_cases=1,
        failed_cases=1,
        skipped_cases=1,
    )
    return [suite]


def test_terminal_reporter() -> None:
    """Verify TerminalReporter formatting and console printing."""
    results = _create_mock_results()
    console = Console(record=True, force_terminal=False)
    reporter = TerminalReporter(console)

    out = reporter.generate(results)
    assert "Passing Test" in out
    assert "Failing Test" in out
    assert "Skipped Test" in out
    assert "Total Tests" in out or "Tests: 3" in out

    reporter.print_results(results)


def test_html_reporter() -> None:
    """Verify HtmlReporter produces valid HTML with summaries and tables."""
    results = _create_mock_results()
    reporter = HtmlReporter()
    html_out = reporter.generate(results)

    assert "<!DOCTYPE html>" in html_out
    assert "API Test Framework Report" in html_out
    assert "Passing Test" in html_out
    assert "Failing Test" in html_out
    assert "FAILED" in html_out
    assert "assert-table" in html_out


def test_junit_reporter() -> None:
    """Verify JunitReporter produces valid JUnit XML compliant with CI."""
    results = _create_mock_results()
    reporter = JunitReporter()
    xml_out = reporter.generate(results)

    assert xml_out.startswith("<?xml")
    root = ET.fromstring(xml_out.split("\n", 1)[1])
    assert root.tag == "testsuites"
    assert root.attrib["tests"] == "3"
    assert root.attrib["failures"] == "1"
    assert root.attrib["skipped"] == "1"

    suite_elem = root.find("testsuite")
    assert suite_elem is not None
    assert suite_elem.attrib["name"] == "Auth Suite"

    cases = suite_elem.findall("testcase")
    assert len(cases) == 3


def test_json_reporter() -> None:
    """Verify JsonReporter produces valid JSON with summary metrics."""
    results = _create_mock_results()
    reporter = JsonReporter()
    json_out = reporter.generate(results)

    data = json.loads(json_out)
    assert "summary" in data
    assert data["summary"]["total_cases"] == 3
    assert data["summary"]["passed_cases"] == 1
    assert data["summary"]["failed_cases"] == 1
    assert data["summary"]["skipped_cases"] == 1
    assert data["summary"]["passed"] is False
    assert len(data["suites"]) == 1
