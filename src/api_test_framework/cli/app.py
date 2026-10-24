"""Click command-line interface for api-test-framework."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import click
from rich.console import Console

from api_test_framework.cli.template import INIT_YAML_TEMPLATE
from api_test_framework.config import FrameworkConfig
from api_test_framework.exceptions import DSLValidationError
from api_test_framework.loader import load_test_suite
from api_test_framework.reporting.html import HtmlReporter
from api_test_framework.reporting.json_report import JsonReporter
from api_test_framework.reporting.junit import JunitReporter
from api_test_framework.reporting.terminal import TerminalReporter
from api_test_framework.runner.chain import SuiteExecutor
from api_test_framework.runner.parallel import ParallelExecutor

if TYPE_CHECKING:
    from api_test_framework.models.result import TestSuiteResult
    from api_test_framework.models.test_suite import TestSuiteModel

console = Console()


@click.group()
@click.version_option(package_name="api-test-framework")
def cli() -> None:
    """REST API Testing Framework CLI."""


def _find_suite_files(target_path: Path) -> list[Path]:
    """Locate all YAML/JSON test files at target path or inside target directory."""
    if target_path.is_file():
        return [target_path]
    if target_path.is_dir():
        files: list[Path] = []
        for ext in ("*.yaml", "*.yml", "*.json"):
            files.extend(target_path.glob(ext))
            files.extend(target_path.glob(f"**/{ext}"))
        # Deduplicate while preserving order
        unique_files: list[Path] = []
        seen = set()
        for f in sorted(files):
            resolved = f.resolve()
            if resolved not in seen:
                seen.add(resolved)
                unique_files.append(f)
        return unique_files
    return []


@cli.command("run")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--base-url", "-u", default=None, help="Base URL override for API requests.")
@click.option(
    "--env-file",
    "-e",
    default=None,
    type=click.Path(exists=True, path_type=Path),
    help="Path to .env configuration file.",
)
@click.option(
    "--report-html",
    "--html",
    default=None,
    type=click.Path(path_type=Path),
    help="Output path for HTML report.",
)
@click.option(
    "--report-junit",
    "--junit",
    default=None,
    type=click.Path(path_type=Path),
    help="Output path for JUnit XML report.",
)
@click.option(
    "--report-json",
    "--json",
    default=None,
    type=click.Path(path_type=Path),
    help="Output path for JSON report.",
)
@click.option(
    "--parallel", "-p", is_flag=True, default=False, help="Run test suites concurrently."
)
@click.option(
    "--workers", "-w", default=4, type=int, help="Worker concurrency when running parallel."
)
@click.option(
    "--verbose", "-v", is_flag=True, default=False, help="Enable verbose console details."
)
def run_command(
    path: Path,
    base_url: str | None,
    env_file: Path | None,
    report_html: Path | None,
    report_junit: Path | None,
    report_json: Path | None,
    parallel: bool,
    workers: int,
    verbose: bool,
) -> None:
    """Execute API test suites from file or directory."""
    files = _find_suite_files(path)
    if not files:
        console.print(
            f"[red]Error:[/red] No test suite files (.yaml, .yml, .json) found at '{path}'"
        )
        sys.exit(1)

    config = FrameworkConfig.from_env(str(env_file) if env_file else None)
    if base_url:
        config.base_url = base_url

    suites: list[TestSuiteModel] = []
    for f in files:
        try:
            suite = load_test_suite(f)
            suites.append(suite)
        except Exception as exc:
            console.print(f"[red]Failed to load test suite '{f}':[/red] {exc}")
            sys.exit(1)

    results: list[TestSuiteResult] = []
    if parallel and len(suites) > 1:
        parallel_executor = ParallelExecutor(config=config, max_workers=workers)
        results = parallel_executor.run_suites(suites, base_url_override=base_url)
    else:
        suite_executor = SuiteExecutor(config=config)
        for suite in suites:
            res = suite_executor.run_suite(suite, base_url_override=base_url)
            results.append(res)

    terminal_reporter = TerminalReporter(console)
    terminal_reporter.print_results(results)

    # Save additional reports if requested
    if report_html:
        html_reporter = HtmlReporter()
        report_html.write_text(html_reporter.generate(results), encoding="utf-8")
        console.print(f"[green]HTML report saved to:[/green] {report_html}")

    if report_junit:
        junit_reporter = JunitReporter()
        report_junit.write_text(junit_reporter.generate(results), encoding="utf-8")
        console.print(f"[green]JUnit XML report saved to:[/green] {report_junit}")

    if report_json:
        json_reporter = JsonReporter()
        report_json.write_text(json_reporter.generate(results), encoding="utf-8")
        console.print(f"[green]JSON report saved to:[/green] {report_json}")

    any_failed = any(not r.passed for r in results)
    if any_failed:
        sys.exit(1)


@cli.command("validate")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def validate_command(path: Path) -> None:
    """Validate YAML or JSON test suite syntax and schema without sending requests."""
    files = _find_suite_files(path)
    if not files:
        console.print(f"[red]Error:[/red] No test suite files found at '{path}'")
        sys.exit(1)

    all_valid = True
    for f in files:
        try:
            suite = load_test_suite(f)
            console.print(
                f"[green]✓ Valid:[/green] {f} (Suite: '[bold]{suite.name}[/bold]' with {len(suite.test_cases)} tests)"
            )
        except DSLValidationError as exc:
            all_valid = False
            console.print(f"[red]✗ Invalid:[/red] {f}\n  {exc}")
        except Exception as exc:
            all_valid = False
            console.print(f"[red]✗ Error loading {f}:[/red] {exc}")

    if not all_valid:
        sys.exit(1)


@cli.command("init")
@click.argument("filename", default="test_api.yaml", type=click.Path(path_type=Path))
def init_command(filename: Path) -> None:
    """Scaffold a starter YAML test suite file."""
    if filename.exists():
        console.print(f"[yellow]Warning:[/yellow] File '{filename}' already exists. Aborting.")
        sys.exit(1)

    filename.write_text(INIT_YAML_TEMPLATE, encoding="utf-8")
    console.print(
        f"[green]Successfully created starter API test suite:[/green] [bold]{filename}[/bold]"
    )
    console.print("Run it with: [cyan]api-test run " + str(filename) + "[/cyan]")
