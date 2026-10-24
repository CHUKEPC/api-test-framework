"""Custom exception classes for api-test-framework."""

from typing import Any


class ApiTestFrameworkError(Exception):
    """Base exception for all api-test-framework errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize base exception with message and optional details.

        Args:
            message: Human-readable error message.
            details: Optional dictionary containing additional error context.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DSLValidationError(ApiTestFrameworkError):
    """Raised when YAML or JSON test suite definition is invalid."""


class ConfigurationError(ApiTestFrameworkError):
    """Raised when configuration parameters are invalid or missing."""


class VariableError(ApiTestFrameworkError):
    """Raised when variable substitution or template rendering fails."""


class VariableExtractionError(VariableError):
    """Raised when a variable cannot be extracted from HTTP response."""


class HttpRequestError(ApiTestFrameworkError):
    """Raised when an HTTP request fails due to network, timeout, or protocol error."""


class AuthenticationError(ApiTestFrameworkError):
    """Raised when authentication setup or token generation fails."""


class AssertionFailedError(ApiTestFrameworkError):
    """Raised when one or more assertions fail for a test case."""

    def __init__(
        self,
        message: str,
        case_name: str = "",
        assertion_type: str = "",
        expected: Any = None,
        actual: Any = None,
    ) -> None:
        """Initialize assertion failure error with specifics.

        Args:
            message: Explanation of failure.
            case_name: Name of test case where assertion failed.
            assertion_type: Type of assertion (status, jsonpath, header, etc.).
            expected: Expected value.
            actual: Actual value received.
        """
        details = {
            "case_name": case_name,
            "assertion_type": assertion_type,
            "expected": expected,
            "actual": actual,
        }
        super().__init__(message, details=details)
        self.case_name = case_name
        self.assertion_type = assertion_type
        self.expected = expected
        self.actual = actual
