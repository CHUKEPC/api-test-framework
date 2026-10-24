"""Execution result models for test suites, cases, and assertions."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from api_test_framework.models.response import HttpResponseData


class AssertionResult(BaseModel):
    """Outcome of a single evaluated assertion."""

    name: str = Field(description="Descriptive name of the assertion")
    assertion_type: str = Field(
        default="general", description="Category: status, header, jsonpath, body, timing, schema"
    )
    passed: bool = Field(description="True if assertion satisfied, False otherwise")
    expected: Any = Field(default=None, description="Expected value or rule")
    actual: Any = Field(default=None, description="Actual value encountered")
    message: str = Field(default="", description="Detailed message explaining result")

    model_config = {
        "arbitrary_types_allowed": True,
    }


class TestCaseResult(BaseModel):
    """Aggregate result for a single test case execution."""

    __test__ = False

    case_name: str = Field(description="Identifier or name of test case")
    suite_name: str = Field(default="", description="Name of parent test suite")
    passed: bool = Field(description="Overall pass status for test case")
    duration_seconds: float = Field(default=0.0, description="Total run time in seconds")
    assertion_results: list[AssertionResult] = Field(
        default_factory=list, description="List of individual assertion results"
    )
    extracted_variables: dict[str, Any] = Field(
        default_factory=dict, description="Variables captured during this step"
    )
    error_message: str | None = Field(
        default=None, description="Error message if an exception was raised"
    )
    response: HttpResponseData | None = Field(
        default=None, description="Captured HTTP response data"
    )
    skipped: bool = Field(default=False, description="Whether test case was skipped")
    skip_reason: str | None = Field(default=None, description="Reason why test case was skipped")

    model_config = {
        "arbitrary_types_allowed": True,
    }


class TestSuiteResult(BaseModel):
    """Summary and details of an entire test suite execution."""

    __test__ = False

    suite_name: str = Field(description="Name of test suite")
    case_results: list[TestCaseResult] = Field(
        default_factory=list, description="List of test case results"
    )
    duration_seconds: float = Field(default=0.0, description="Total execution duration")
    passed: bool = Field(default=True, description="True if all test cases passed")
    total_cases: int = Field(default=0, description="Total test cases in suite")
    passed_cases: int = Field(default=0, description="Count of passed test cases")
    failed_cases: int = Field(default=0, description="Count of failed test cases")
    skipped_cases: int = Field(default=0, description="Count of skipped test cases")

    model_config = {
        "arbitrary_types_allowed": True,
    }
