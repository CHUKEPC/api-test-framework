"""Shared test fixtures for api-test-framework test suite."""

from __future__ import annotations

import pytest

from api_test_framework.config import FrameworkConfig
from api_test_framework.models.assertion import AssertionModel, JsonPathAssertionModel
from api_test_framework.models.request import HttpRequestModel
from api_test_framework.models.response import HttpResponseData
from api_test_framework.models.test_case import TestCaseModel, VariableExtractionModel
from api_test_framework.models.test_suite import HookModel, TestSuiteModel
from api_test_framework.variables import VariableManager


@pytest.fixture
def sample_response_data() -> HttpResponseData:
    """Fixture providing a mock HttpResponseData object."""
    return HttpResponseData(
        status_code=200,
        headers={
            "Content-Type": "application/json",
            "X-Server": "MockServer/1.0",
        },
        body={
            "id": 101,
            "name": "Antigravity",
            "email": "antigravity@deepmind.com",
            "active": True,
            "roles": ["admin", "developer"],
            "profile": {
                "age": 28,
                "city": "London",
            },
        },
        text='{"id": 101, "name": "Antigravity", "email": "antigravity@deepmind.com", "active": true, "roles": ["admin", "developer"], "profile": {"age": 28, "city": "London"}}',
        elapsed_seconds=0.15,
        url="https://api.example.com/users/101",
        method="GET",
        cookies={"session": "abc123xyz"},
    )


@pytest.fixture
def sample_test_case() -> TestCaseModel:
    """Fixture providing a valid TestCaseModel instance."""
    return TestCaseModel(
        id="case-1",
        name="Get User Details",
        description="Verify user retrieval by id",
        tags=["smoke", "users"],
        request=HttpRequestModel(
            method="GET",
            url="/users/{user_id}",
            path_params={"user_id": 101},
        ),
        assertions=AssertionModel(
            status_code=200,
            jsonpath=[
                JsonPathAssertionModel(path="$.id", op="equals", expected=101),
                JsonPathAssertionModel(path="$.name", op="equals", expected="Antigravity"),
            ],
            max_duration=1.0,
        ),
        extract=[
            VariableExtractionModel(
                name="captured_email",
                source="jsonpath",
                expression="$.email",
            )
        ],
    )


@pytest.fixture
def sample_test_suite(sample_test_case: TestCaseModel) -> TestSuiteModel:
    """Fixture providing a valid TestSuiteModel instance."""
    return TestSuiteModel(
        name="User Management Suite",
        description="Tests user operations",
        base_url="https://api.example.com",
        headers={"Accept": "application/json"},
        variables={"default_role": "viewer"},
        hooks=HookModel(
            setup=[],
            teardown=[],
        ),
        tests=[sample_test_case],
    )


@pytest.fixture
def default_config() -> FrameworkConfig:
    """Fixture providing default FrameworkConfig."""
    return FrameworkConfig(
        base_url="https://api.example.com",
        timeout=10.0,
        verify_ssl=True,
    )


@pytest.fixture
def var_manager() -> VariableManager:
    """Fixture providing an empty VariableManager."""
    return VariableManager()
