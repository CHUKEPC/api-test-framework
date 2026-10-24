"""JSON report generator for machine-readable test execution outcomes."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from api_test_framework.reporting.base import BaseReporter

if TYPE_CHECKING:
    from collections.abc import Sequence

    from api_test_framework.models.result import TestSuiteResult


class JsonReporter(BaseReporter):
    """Generates structured JSON reports containing detailed execution data."""

    def generate(self, results: Sequence[TestSuiteResult]) -> str:
        """Render results into formatted JSON string.

        Args:
            results: Sequence of TestSuiteResult objects.

        Returns:
            JSON string representation.
        """
        total_cases = sum(r.total_cases for r in results)
        passed_cases = sum(r.passed_cases for r in results)
        failed_cases = sum(r.failed_cases for r in results)
        skipped_cases = sum(r.skipped_cases for r in results)
        total_time = sum(r.duration_seconds for r in results)

        data = {
            "summary": {
                "total_suites": len(results),
                "total_cases": total_cases,
                "passed_cases": passed_cases,
                "failed_cases": failed_cases,
                "skipped_cases": skipped_cases,
                "passed": failed_cases == 0,
                "duration_seconds": round(total_time, 4),
            },
            "suites": [suite.model_dump() for suite in results],
        }
        return json.dumps(data, indent=2, default=str)
