"""HTML report generator for API test execution."""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

from api_test_framework.reporting.base import BaseReporter

if TYPE_CHECKING:
    from collections.abc import Sequence

    from api_test_framework.models.result import TestSuiteResult


class HtmlReporter(BaseReporter):
    """Generates self-contained interactive HTML reports."""

    def generate(self, results: Sequence[TestSuiteResult]) -> str:
        """Produce full HTML document string containing test outcomes and assertion traces.

        Args:
            results: Sequence of completed TestSuiteResult models.

        Returns:
            HTML source string.
        """
        total_cases = sum(r.total_cases for r in results)
        passed_cases = sum(r.passed_cases for r in results)
        failed_cases = sum(r.failed_cases for r in results)
        skipped_cases = sum(r.skipped_cases for r in results)
        total_time = sum(r.duration_seconds for r in results)

        overall_status = "PASSED" if failed_cases == 0 else "FAILED"
        overall_badge_class = "badge-pass" if failed_cases == 0 else "badge-fail"

        suite_sections: list[str] = []

        for suite in results:
            case_rows: list[str] = []
            for case in suite.case_results:
                if case.skipped:
                    badge = '<span class="badge badge-skip">SKIPPED</span>'
                elif case.passed:
                    badge = '<span class="badge badge-pass">PASSED</span>'
                else:
                    badge = '<span class="badge badge-fail">FAILED</span>'

                assert_rows: list[str] = []
                for a in case.assertion_results:
                    a_badge = (
                        '<span class="badge-mini pass">✓</span>'
                        if a.passed
                        else '<span class="badge-mini fail">✗</span>'
                    )
                    assert_rows.append(
                        f"<tr><td>{a_badge}</td><td>{html.escape(a.name)}</td>"
                        f"<td>{html.escape(str(a.expected))}</td><td>{html.escape(str(a.actual))}</td>"
                        f"<td>{html.escape(a.message)}</td></tr>"
                    )

                assert_table = ""
                if assert_rows:
                    assert_table = f"""
                    <table class="assert-table">
                        <thead><tr><th></th><th>Assertion</th><th>Expected</th><th>Actual</th><th>Message</th></tr></thead>
                        <tbody>{"".join(assert_rows)}</tbody>
                    </table>
                    """

                error_box = ""
                if case.error_message:
                    error_box = f'<div class="error-box"><strong>Error:</strong> {html.escape(case.error_message)}</div>'

                case_rows.append(f"""
                <div class="case-card">
                    <div class="case-header">
                        <span class="case-title">{html.escape(case.case_name)}</span>
                        <div class="case-meta">
                            {badge}
                            <span class="duration">{case.duration_seconds * 1000:.1f}ms</span>
                        </div>
                    </div>
                    {error_box}
                    {assert_table}
                </div>
                """)

            suite_sections.append(f"""
            <div class="suite-section">
                <h2>Suite: {html.escape(suite.suite_name)}</h2>
                <div class="suite-meta">
                    Duration: {suite.duration_seconds:.2f}s | Cases: {suite.total_cases} |
                    Passed: {suite.passed_cases} | Failed: {suite.failed_cases}
                </div>
                {"".join(case_rows)}
            </div>
            """)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>API Test Framework Report</title>
    <style>
        :root {{
            --bg: #f8fafc;
            --text: #0f172a;
            --card-bg: #ffffff;
            --border: #e2e8f0;
            --pass: #10b981;
            --fail: #ef4444;
            --skip: #f59e0b;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 24px;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        header {{
            background: var(--card-bg);
            padding: 24px;
            border-radius: 8px;
            border: 1px solid var(--border);
            margin-bottom: 24px;
        }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 16px;
            margin-top: 16px;
        }}
        .card {{
            background: var(--bg);
            padding: 16px;
            border-radius: 6px;
            text-align: center;
        }}
        .card-val {{ font-size: 24px; font-weight: bold; }}
        .badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            color: white;
        }}
        .badge-pass {{ background: var(--pass); }}
        .badge-fail {{ background: var(--fail); }}
        .badge-skip {{ background: var(--skip); }}
        .badge-mini {{ font-weight: bold; font-size: 14px; }}
        .badge-mini.pass {{ color: var(--pass); }}
        .badge-mini.fail {{ color: var(--fail); }}
        .suite-section {{
            background: var(--card-bg);
            padding: 20px;
            border-radius: 8px;
            border: 1px solid var(--border);
            margin-bottom: 20px;
        }}
        .case-card {{
            border-top: 1px solid var(--border);
            padding: 14px 0;
        }}
        .case-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .case-title {{ font-weight: 600; font-size: 16px; }}
        .duration {{ color: #64748b; font-size: 13px; margin-left: 8px; }}
        .assert-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 13px;
        }}
        .assert-table th, .assert-table td {{
            text-align: left;
            padding: 6px 8px;
            border-bottom: 1px solid #f1f5f9;
        }}
        .assert-table th {{ background: #f8fafc; font-weight: 600; }}
        .error-box {{
            background: #fee2e2;
            color: #991b1b;
            padding: 10px;
            border-radius: 4px;
            margin-top: 8px;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>API Test Framework Report</h1>
            <span class="badge {overall_badge_class}">{overall_status}</span>
            <div class="summary-cards">
                <div class="card"><div class="card-val">{total_cases}</div>Total Tests</div>
                <div class="card"><div class="card-val" style="color:var(--pass)">{passed_cases}</div>Passed</div>
                <div class="card"><div class="card-val" style="color:var(--fail)">{failed_cases}</div>Failed</div>
                <div class="card"><div class="card-val" style="color:var(--skip)">{skipped_cases}</div>Skipped</div>
                <div class="card"><div class="card-val">{total_time:.2f}s</div>Duration</div>
            </div>
        </header>
        {"".join(suite_sections)}
    </div>
</body>
</html>"""
        return html_content
