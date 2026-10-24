"""Rich terminal test reporter with colorful tables and summaries."""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from api_test_framework.reporting.base import BaseReporter

if TYPE_CHECKING:
    from collections.abc import Sequence

    from api_test_framework.models.result import TestSuiteResult


class TerminalReporter(BaseReporter):
    """Generates formatted ANSI/plain text terminal output via Rich."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize terminal reporter.

        Args:
            console: Optional Rich Console instance.
        """
        self.console = console or Console(record=True, force_terminal=True)

    def generate(self, results: Sequence[TestSuiteResult]) -> str:
        """Format test results into Rich terminal display and capture string.

        Args:
            results: Sequence of TestSuiteResult objects.

        Returns:
            Console output text.
        """
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=False, width=100)

        total_suites = len(results)
        total_cases = sum(r.total_cases for r in results)
        passed_cases = sum(r.passed_cases for r in results)
        failed_cases = sum(r.failed_cases for r in results)
        skipped_cases = sum(r.skipped_cases for r in results)
        total_duration = sum(r.duration_seconds for r in results)

        table = Table(title="API Test Framework Execution Summary", show_header=True)
        table.add_column("Suite", style="bold cyan")
        table.add_column("Case", style="white")
        table.add_column("Status", justify="center")
        table.add_column("Duration", justify="right")
        table.add_column("Details", style="dim")

        for suite_res in results:
            for case_res in suite_res.case_results:
                if case_res.skipped:
                    status = "[yellow]SKIPPED[/yellow]"
                    details = case_res.skip_reason or ""
                elif case_res.passed:
                    status = "[green]PASSED[/green]"
                    details = f"{len(case_res.assertion_results)} assertions"
                else:
                    status = "[red]FAILED[/red]"
                    if case_res.error_message:
                        details = case_res.error_message[:40]
                    else:
                        failed_asserts = [a for a in case_res.assertion_results if not a.passed]
                        details = (
                            failed_asserts[0].message[:40] if failed_asserts else "Unknown failure"
                        )

                table.add_row(
                    suite_res.suite_name,
                    case_res.case_name,
                    status,
                    f"{case_res.duration_seconds * 1000:.1f}ms",
                    details,
                )

        console.print(table)

        summary_style = "green" if failed_cases == 0 else "red"
        summary_text = (
            f"Suites: {total_suites} | Tests: {total_cases} | "
            f"Passed: {passed_cases} | Failed: {failed_cases} | "
            f"Skipped: {skipped_cases} | Time: {total_duration:.2f}s"
        )
        console.print(Panel(summary_text, style=summary_style, title="Test Run Outcome"))

        return buffer.getvalue()

    def print_results(self, results: Sequence[TestSuiteResult]) -> None:
        """Directly print formatted results to the terminal console.

        Args:
            results: Sequence of TestSuiteResult objects.
        """
        out = self.generate(results)
        self.console.print(out)
