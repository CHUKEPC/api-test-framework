"""Sequential test suite execution with variable chaining and hooks."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

import httpx

from api_test_framework.assertions import evaluate_assertions
from api_test_framework.config import FrameworkConfig
from api_test_framework.models.request import HttpRequestModel
from api_test_framework.models.result import (
    AssertionResult,
    TestCaseResult,
    TestSuiteResult,
)
from api_test_framework.runner.executor import HttpExecutor
from api_test_framework.variables import VariableManager

if TYPE_CHECKING:
    from api_test_framework.models.test_case import TestCaseModel
    from api_test_framework.models.test_suite import TestSuiteModel


class SuiteExecutor:
    """Executes a test suite sequentially, chaining extracted variables between steps."""

    def __init__(
        self,
        config: FrameworkConfig | None = None,
        initial_variables: dict[str, Any] | None = None,
    ) -> None:
        """Initialize suite executor.

        Args:
            config: FrameworkConfig runtime options.
            initial_variables: Optional global variables to inject into context.
        """
        self.config = config or FrameworkConfig()
        self.initial_variables = dict(initial_variables or {})
        self.executor = HttpExecutor(self.config)

    def _render_request(
        self,
        request: HttpRequestModel,
        variable_manager: VariableManager,
    ) -> HttpRequestModel:
        """Render all dynamic template expressions inside an HttpRequestModel."""
        url = str(variable_manager.render(request.url))
        path_params = variable_manager.render(request.path_params)
        query_params = variable_manager.render(request.query_params)
        headers = variable_manager.render(request.headers)
        cookies = variable_manager.render(request.cookies)
        json_body = (
            variable_manager.render(request.json_body) if request.json_body is not None else None
        )
        data = variable_manager.render(request.data) if request.data is not None else None

        auth = request.auth
        if auth is not None:
            auth_dict = variable_manager.render(auth.model_dump())
            auth = type(auth).model_validate(auth_dict)

        return HttpRequestModel(
            method=request.method,
            url=url,
            path_params=path_params,
            query_params=query_params,
            headers=headers,
            cookies=cookies,
            json=json_body,
            data=data,
            auth=auth,
            timeout=request.timeout,
            verify_ssl=request.verify_ssl,
            follow_redirects=request.follow_redirects,
        )

    async def execute_case(
        self,
        case: TestCaseModel,
        suite_name: str,
        base_url: str | None,
        variable_manager: VariableManager,
        client: httpx.AsyncClient | None = None,
    ) -> TestCaseResult:
        """Execute a single test case within the suite context.

        Args:
            case: TestCaseModel specification.
            suite_name: Parent suite name.
            base_url: Suite or global base URL.
            variable_manager: Context variable manager.
            client: Optional reusable HTTP client.

        Returns:
            TestCaseResult with outcome, timings, and assertion results.
        """
        if case.skip:
            reason = str(case.skip) if isinstance(case.skip, str) else "Skipped by configuration"
            return TestCaseResult(
                case_name=case.name,
                suite_name=suite_name,
                passed=True,
                duration_seconds=0.0,
                skipped=True,
                skip_reason=reason,
            )

        if case.delay_before > 0:
            await asyncio.sleep(case.delay_before)

        case_start = time.perf_counter()
        assertion_results: list[AssertionResult] = []
        extracted: dict[str, Any] = {}
        error_msg: str | None = None
        response = None

        try:
            rendered_request = self._render_request(case.request, variable_manager)
            response = await self.executor.execute_request(
                request=rendered_request,
                base_url=base_url,
                retries=case.retries,
                retry_delay=case.retry_delay,
                client=client,
            )

            # Evaluate assertions
            assertion_results = evaluate_assertions(
                case.assertions,
                response,
                variable_manager,
            )

            passed = all(r.passed for r in assertion_results) if assertion_results else True

            # If passed, extract variables for chained steps
            if passed:
                for extraction in case.extract:
                    val = variable_manager.extract(
                        source=extraction.source,
                        expression=extraction.expression,
                        response=response,
                        default=extraction.default,
                    )
                    variable_manager.set(extraction.name, val)
                    extracted[extraction.name] = val

        except Exception as exc:
            passed = False
            error_msg = str(exc)

        if case.delay_after > 0:
            await asyncio.sleep(case.delay_after)

        duration = time.perf_counter() - case_start

        return TestCaseResult(
            case_name=case.name,
            suite_name=suite_name,
            passed=passed,
            duration_seconds=duration,
            assertion_results=assertion_results,
            extracted_variables=extracted,
            error_message=error_msg,
            response=response,
            skipped=False,
        )

    async def run_suite_async(
        self,
        suite: TestSuiteModel,
        base_url_override: str | None = None,
    ) -> TestSuiteResult:
        """Run all test cases in the test suite sequentially with lifecycle hooks.

        Args:
            suite: TestSuiteModel definition.
            base_url_override: Optional base URL override from CLI or runner.

        Returns:
            Aggregated TestSuiteResult.
        """
        start_time = time.perf_counter()

        # Merge variables: initial -> suite-level
        combined_vars = dict(self.initial_variables)
        combined_vars.update(suite.variables)
        variable_manager = VariableManager(combined_vars)

        effective_base_url = base_url_override or suite.base_url or self.config.base_url

        case_results: list[TestCaseResult] = []

        verify_ssl = self.config.verify_ssl
        async with httpx.AsyncClient(verify=verify_ssl) as client:
            # 1. Run Setup Hooks
            for setup_req in suite.hooks.setup:
                rendered_setup = self._render_request(setup_req, variable_manager)
                await self.executor.execute_request(
                    rendered_setup,
                    base_url=effective_base_url,
                    client=client,
                )

            # 2. Run Test Cases
            try:
                for case in suite.test_cases:
                    case_res = await self.execute_case(
                        case=case,
                        suite_name=suite.name,
                        base_url=effective_base_url,
                        variable_manager=variable_manager,
                        client=client,
                    )
                    case_results.append(case_res)
            finally:
                # 3. Run Teardown Hooks
                for teardown_req in suite.hooks.teardown:
                    try:
                        rendered_teardown = self._render_request(teardown_req, variable_manager)
                        await self.executor.execute_request(
                            rendered_teardown,
                            base_url=effective_base_url,
                            client=client,
                        )
                    except Exception:
                        pass

        total_duration = time.perf_counter() - start_time
        total_cases = len(case_results)
        passed_cases = sum(1 for c in case_results if c.passed and not c.skipped)
        failed_cases = sum(1 for c in case_results if not c.passed and not c.skipped)
        skipped_cases = sum(1 for c in case_results if c.skipped)
        all_passed = failed_cases == 0

        return TestSuiteResult(
            suite_name=suite.name,
            case_results=case_results,
            duration_seconds=total_duration,
            passed=all_passed,
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            skipped_cases=skipped_cases,
        )

    def run_suite(
        self,
        suite: TestSuiteModel,
        base_url_override: str | None = None,
    ) -> TestSuiteResult:
        """Synchronous wrapper for running a test suite.

        Args:
            suite: TestSuiteModel definition.
            base_url_override: Optional base URL override.

        Returns:
            TestSuiteResult.
        """
        return asyncio.run(self.run_suite_async(suite, base_url_override))
