"""JUnit XML report generator for CI/CD integration."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

from api_test_framework.reporting.base import BaseReporter

if TYPE_CHECKING:
    from collections.abc import Sequence

    from api_test_framework.models.result import TestSuiteResult


class JunitReporter(BaseReporter):
    """Generates standard JUnit XML files compatible with CI pipelines."""

    def generate(self, results: Sequence[TestSuiteResult]) -> str:
        """Render results into a valid JUnit XML string.

        Args:
            results: Sequence of TestSuiteResult objects.

        Returns:
            XML string representation.
        """
        root = ET.Element("testsuites")
        total_tests = sum(r.total_cases for r in results)
        total_failures = sum(r.failed_cases for r in results)
        total_skipped = sum(r.skipped_cases for r in results)
        total_time = sum(r.duration_seconds for r in results)

        root.set("tests", str(total_tests))
        root.set("failures", str(total_failures))
        root.set("errors", "0")
        root.set("skipped", str(total_skipped))
        root.set("time", f"{total_time:.3f}")

        for suite in results:
            ts = ET.SubElement(root, "testsuite")
            ts.set("name", suite.suite_name)
            ts.set("tests", str(suite.total_cases))
            ts.set("failures", str(suite.failed_cases))
            ts.set("errors", "0")
            ts.set("skipped", str(suite.skipped_cases))
            ts.set("time", f"{suite.duration_seconds:.3f}")

            for case in suite.case_results:
                tc = ET.SubElement(ts, "testcase")
                tc.set("classname", suite.suite_name)
                tc.set("name", case.case_name)
                tc.set("time", f"{case.duration_seconds:.3f}")

                if case.skipped:
                    skipped_elem = ET.SubElement(tc, "skipped")
                    if case.skip_reason:
                        skipped_elem.set("message", case.skip_reason)
                elif not case.passed:
                    failure_elem = ET.SubElement(tc, "failure")
                    failed_asserts = [a for a in case.assertion_results if not a.passed]
                    if case.error_message:
                        failure_elem.set("message", case.error_message)
                        failure_elem.text = case.error_message
                    elif failed_asserts:
                        failure_elem.set("message", failed_asserts[0].message)
                        failure_elem.text = "\n".join(
                            f"{a.name}: {a.message} (expected={a.expected!r}, actual={a.actual!r})"
                            for a in failed_asserts
                        )
                    else:
                        failure_elem.set("message", "Test case failed")

        xml_str = ET.tostring(root, encoding="utf-8", method="xml").decode("utf-8")
        return f'<?xml version="1.0" encoding="utf-8"?>\n{xml_str}'
