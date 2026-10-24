"""Assertion engine uniting status, header, body, JSONPath, schema, and timing checks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from api_test_framework.assertions.body import (
    assert_body_contains,
    assert_body_deep,
    assert_body_exact,
    assert_body_regex,
)
from api_test_framework.assertions.headers import assert_headers
from api_test_framework.assertions.jsonpath import assert_jsonpath
from api_test_framework.assertions.registry import (
    clear_custom_assertions,
    get_custom_assertion,
    register_custom_assertion,
)
from api_test_framework.assertions.schema import assert_json_schema
from api_test_framework.assertions.status import assert_status_code
from api_test_framework.assertions.timing import assert_max_duration
from api_test_framework.models.result import AssertionResult

if TYPE_CHECKING:
    from api_test_framework.models.assertion import AssertionModel
    from api_test_framework.models.response import HttpResponseData
    from api_test_framework.variables import VariableManager


def evaluate_assertions(
    assertions: AssertionModel,
    response: HttpResponseData,
    variable_manager: VariableManager | None = None,
) -> list[AssertionResult]:
    """Evaluate all configured assertions on an HTTP response.

    Args:
        assertions: Assertion specifications from test case.
        response: Executed HTTP response data.
        variable_manager: Optional VariableManager to render dynamic templates in expectations.

    Returns:
        List of AssertionResult objects for all performed checks.
    """
    results: list[AssertionResult] = []

    # 1. Status code assertion
    if assertions.status_code is not None:
        expected_status = (
            variable_manager.render(assertions.status_code)
            if variable_manager
            else assertions.status_code
        )
        results.append(assert_status_code(expected_status, response.status_code))

    # 2. Header assertions
    if assertions.headers is not None:
        rendered_headers = (
            variable_manager.render(assertions.headers) if variable_manager else assertions.headers
        )
        results.extend(assert_headers(rendered_headers, response.headers))

    # 3. Body exact match
    if assertions.body is not None:
        rendered_body = (
            variable_manager.render(assertions.body) if variable_manager else assertions.body
        )
        if isinstance(rendered_body, (dict, list)) and isinstance(response.body, (dict, list)):
            results.extend(assert_body_deep(rendered_body, response.body))
        else:
            results.append(assert_body_exact(rendered_body, response.body or response.text))

    # 4. Body substring containment
    if assertions.body_contains is not None:
        expected_substring = (
            variable_manager.render(assertions.body_contains)
            if variable_manager
            else assertions.body_contains
        )
        results.append(assert_body_contains(str(expected_substring), response.text))

    # 5. Body regex pattern
    if assertions.body_regex is not None:
        expected_regex = (
            variable_manager.render(assertions.body_regex)
            if variable_manager
            else assertions.body_regex
        )
        results.append(assert_body_regex(str(expected_regex), response.text))

    # 6. JSONPath assertions
    if assertions.jsonpath is not None:
        rendered_jsonpath = (
            variable_manager.render(assertions.jsonpath)
            if variable_manager
            else assertions.jsonpath
        )
        results.extend(assert_jsonpath(rendered_jsonpath, response.body))

    # 7. JSON Schema validation
    if assertions.schema_def is not None:
        rendered_schema = (
            variable_manager.render(assertions.schema_def)
            if variable_manager
            else assertions.schema_def
        )
        results.append(assert_json_schema(rendered_schema, response.body))

    # 8. Maximum duration assertion
    if assertions.max_duration is not None:
        results.append(assert_max_duration(assertions.max_duration, response.elapsed_seconds))

    # 9. Custom assertion functions
    for custom_name in assertions.custom:
        custom_fn = get_custom_assertion(custom_name)
        if custom_fn is not None:
            results.append(custom_fn(response))
        else:
            results.append(
                AssertionResult(
                    name=f"custom:{custom_name}",
                    assertion_type="custom",
                    passed=False,
                    expected=custom_name,
                    actual=None,
                    message=f"Custom assertion '{custom_name}' is not registered",
                )
            )

    return results


__all__ = [
    "assert_body_contains",
    "assert_body_deep",
    "assert_body_exact",
    "assert_body_regex",
    "assert_headers",
    "assert_json_schema",
    "assert_jsonpath",
    "assert_max_duration",
    "assert_status_code",
    "clear_custom_assertions",
    "evaluate_assertions",
    "get_custom_assertion",
    "register_custom_assertion",
]
