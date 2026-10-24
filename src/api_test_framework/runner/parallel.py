"""Parallel execution of test suites using asyncio."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from api_test_framework.config import FrameworkConfig
from api_test_framework.runner.chain import SuiteExecutor

if TYPE_CHECKING:
    from collections.abc import Sequence

    from api_test_framework.models.result import TestSuiteResult
    from api_test_framework.models.test_suite import TestSuiteModel


class ParallelExecutor:
    """Executes multiple test suites concurrently with bounded worker concurrency."""

    def __init__(
        self,
        config: FrameworkConfig | None = None,
        max_workers: int = 4,
    ) -> None:
        """Initialize parallel executor.

        Args:
            config: Optional runtime configuration.
            max_workers: Maximum number of test suites executed concurrently.
        """
        self.config = config or FrameworkConfig()
        self.max_workers = max(1, max_workers)

    async def run_suites_async(
        self,
        suites: Sequence[TestSuiteModel],
        base_url_override: str | None = None,
    ) -> list[TestSuiteResult]:
        """Execute multiple test suites concurrently using asyncio Semaphore.

        Args:
            suites: Sequence of TestSuiteModel specifications.
            base_url_override: Optional base URL override.

        Returns:
            List of TestSuiteResult in order corresponding to input suites.
        """
        semaphore = asyncio.Semaphore(self.max_workers)

        async def _run_single(suite: TestSuiteModel) -> TestSuiteResult:
            async with semaphore:
                suite_exec = SuiteExecutor(self.config)
                return await suite_exec.run_suite_async(suite, base_url_override)

        tasks = [_run_single(suite) for suite in suites]
        return await asyncio.gather(*tasks)

    def run_suites(
        self,
        suites: Sequence[TestSuiteModel],
        base_url_override: str | None = None,
    ) -> list[TestSuiteResult]:
        """Synchronously execute multiple test suites in parallel.

        Args:
            suites: Sequence of TestSuiteModel specifications.
            base_url_override: Optional base URL override.

        Returns:
            List of TestSuiteResult.
        """
        return asyncio.run(self.run_suites_async(suites, base_url_override))
