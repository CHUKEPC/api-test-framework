"""Model defining a test suite comprising multiple test cases and shared config."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from api_test_framework.models.request import AuthModel, HttpRequestModel
from api_test_framework.models.test_case import TestCaseModel


class HookModel(BaseModel):
    """Setup and teardown HTTP requests for test suite lifecycle."""

    setup: list[HttpRequestModel] = Field(
        default_factory=list, description="Requests to execute prior to running suite cases"
    )
    teardown: list[HttpRequestModel] = Field(
        default_factory=list, description="Requests to execute after running suite cases"
    )


class TestSuiteModel(BaseModel):
    """Root model for an API test suite specification."""

    __test__ = False

    name: str = Field(description="Name of the test suite")
    description: str | None = Field(default=None, description="Overview of the test suite")
    base_url: str | None = Field(
        default=None, description="Base URL prepended to relative request URLs"
    )
    headers: dict[str, str] = Field(
        default_factory=dict, description="Default headers applied to all suite requests"
    )
    variables: dict[str, Any] = Field(
        default_factory=dict, description="Initial suite-level variable definitions"
    )
    auth: AuthModel | None = Field(
        default=None, description="Default authentication applied to all suite requests"
    )
    hooks: HookModel = Field(
        default_factory=HookModel, description="Suite setup and teardown lifecycle hooks"
    )
    test_cases: list[TestCaseModel] = Field(
        default_factory=list,
        alias="tests",
        description="Ordered sequence of test cases in this suite",
    )

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
