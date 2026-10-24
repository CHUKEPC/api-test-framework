"""Model definitions for individual test cases and variable extraction."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from api_test_framework.models.assertion import AssertionModel
from api_test_framework.models.request import HttpRequestModel

ExtractionSource = Literal["body", "jsonpath", "header", "regex", "status_code"]


class VariableExtractionModel(BaseModel):
    """Configuration for capturing values from HTTP responses into variable store."""

    name: str = Field(description="Variable name to assign in context")
    source: ExtractionSource = Field(
        default="jsonpath", description="Source location in response to extract from"
    )
    expression: str = Field(
        default="", description="JSONPath, header name, or regex extraction expression"
    )
    default: Any = Field(default=None, description="Fallback value if extraction returns nothing")


class TestCaseModel(BaseModel):
    """Specification of an individual API test case."""

    __test__ = False

    id: str | None = Field(default=None, description="Optional unique identifier")
    name: str = Field(description="Descriptive name of test case")
    description: str | None = Field(
        default=None, description="Detailed explanation of test intent"
    )
    tags: list[str] = Field(default_factory=list, description="Tags or category labels")
    request: HttpRequestModel = Field(description="HTTP request to execute")
    assertions: AssertionModel = Field(
        default_factory=AssertionModel, description="Expected response criteria"
    )
    extract: list[VariableExtractionModel] = Field(
        default_factory=list, description="Variables to extract for subsequent chained tests"
    )
    retries: int = Field(
        default=0, description="Number of retry attempts if request/assertions fail"
    )
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")
    delay_before: float = Field(
        default=0.0, description="Pause duration before executing request in seconds"
    )
    delay_after: float = Field(
        default=0.0, description="Pause duration after executing request in seconds"
    )
    skip: bool | str = Field(
        default=False, description="Flag or reason string to skip this test case"
    )

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
