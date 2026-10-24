"""Models defining assertions on HTTP responses."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class JsonPathAssertionModel(BaseModel):
    """Specification for a single JSONPath assertion."""

    path: str = Field(description="JSONPath expression, e.g. '$.data.id' or '$.items[0].name'")
    op: Literal[
        "equals",
        "not_equals",
        "contains",
        "exists",
        "regex",
        "gt",
        "gte",
        "lt",
        "lte",
        "type",
        "len",
    ] = Field(default="equals", description="Comparison operator to apply")
    expected: Any = Field(default=None, description="Expected value or pattern")


class HeaderAssertionModel(BaseModel):
    """Specification for asserting HTTP response header attributes."""

    name: str = Field(description="Header name (case-insensitive)")
    op: Literal["equals", "contains", "regex", "exists"] = Field(
        default="equals", description="Comparison operator"
    )
    expected: str | None = Field(default=None, description="Expected header value")


class AssertionModel(BaseModel):
    """Aggregated assertion definition for a test case."""

    status_code: int | list[int] | None = Field(
        default=None, description="Expected HTTP status code or acceptable status code list"
    )
    headers: dict[str, Any] | list[HeaderAssertionModel] | None = Field(
        default=None, description="Header assertions (key-value or list of rules)"
    )
    body: Any = Field(
        default=None, description="Expected body (exact value or partial dict/list match)"
    )
    body_contains: str | None = Field(
        default=None, description="Substring expected to appear in response text"
    )
    body_regex: str | None = Field(
        default=None, description="Regular expression pattern expected to match response text"
    )
    jsonpath: dict[str, Any] | list[JsonPathAssertionModel] | None = Field(
        default=None, description="JSONPath assertions (mapping or list of explicit models)"
    )
    schema_def: dict[str, Any] | str | None = Field(
        default=None, alias="schema", description="JSON Schema dict or schema file path"
    )
    max_duration: float | None = Field(
        default=None, description="Maximum allowed response duration in seconds"
    )
    custom: list[str] = Field(
        default_factory=list, description="Names of custom registered assertion functions"
    )

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
