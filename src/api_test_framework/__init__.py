"""api-test-framework: REST API testing framework with YAML DSL, pytest plugin, and rich reporting.

This library provides declarative API testing capabilities, rich assertion engines,
variable chaining, authentication helpers, and seamless pytest integration.
"""

from api_test_framework.config import FrameworkConfig
from api_test_framework.exceptions import (
    ApiTestFrameworkError,
    AssertionFailedError,
    DSLValidationError,
    HttpRequestError,
    VariableError,
    VariableExtractionError,
)
from api_test_framework.loader.yaml_loader import load_test_suite_from_yaml
from api_test_framework.models.test_suite import TestSuiteModel
from api_test_framework.runner.chain import SuiteExecutor
from api_test_framework.runner.executor import HttpExecutor
from api_test_framework.variables import VariableManager

__version__ = "0.1.0"

__all__ = [
    "ApiTestFrameworkError",
    "AssertionFailedError",
    "DSLValidationError",
    "FrameworkConfig",
    "HttpExecutor",
    "HttpRequestError",
    "SuiteExecutor",
    "TestSuiteModel",
    "VariableError",
    "VariableExtractionError",
    "VariableManager",
    "load_test_suite_from_yaml",
]
