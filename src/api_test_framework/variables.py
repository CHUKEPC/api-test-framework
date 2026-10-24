"""Variable management, extraction, and template substitution engine."""

from __future__ import annotations

import datetime
import os
import random
import re
import string
import time
import uuid
from typing import TYPE_CHECKING, Any

import jinja2
from jinja2.nativetypes import NativeEnvironment
from jsonpath_ng.ext.parser import parse as parse_jsonpath

from api_test_framework.exceptions import VariableError, VariableExtractionError

if TYPE_CHECKING:
    from api_test_framework.models.response import HttpResponseData


def _generate_uuid() -> str:
    """Generate a random UUID v4 string."""
    return str(uuid.uuid4())


def _current_timestamp() -> int:
    """Return current Unix timestamp in seconds."""
    return int(time.time())


def _random_integer(min_val: int = 1, max_val: int = 100000) -> int:
    """Generate a random integer between min_val and max_val inclusive."""
    return random.randint(min_val, max_val)


def _random_string(length: int = 8) -> str:
    """Generate a random lowercase alphanumeric string."""
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def _now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.datetime.now(datetime.UTC).isoformat()


class VariableManager:
    """Manages variable context, Jinja2 template rendering, and response extraction."""

    def __init__(self, initial_variables: dict[str, Any] | None = None) -> None:
        """Initialize variable manager with optional initial variables.

        Args:
            initial_variables: Initial key-value pairs for the execution context.
        """
        self._store: dict[str, Any] = dict(initial_variables or {})
        self._env: NativeEnvironment = NativeEnvironment(
            undefined=jinja2.StrictUndefined,
            autoescape=False,
        )
        # Register custom helper functions
        self._env.globals.update(
            {
                "uuid": _generate_uuid,
                "timestamp": _current_timestamp,
                "random_int": _random_integer,
                "random_str": _random_string,
                "now_iso": _now_iso,
            }
        )

    def set(self, key: str, value: Any) -> None:
        """Store a variable in context.

        Args:
            key: Variable name.
            value: Variable value.
        """
        self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a variable from context or OS environment.

        Args:
            key: Variable name.
            default: Fallback if variable is missing.

        Returns:
            Resolved variable value or default.
        """
        if key in self._store:
            return self._store[key]
        if key in os.environ:
            return os.environ[key]
        return default

    def all_variables(self) -> dict[str, Any]:
        """Return a copy of all stored variables plus system environment mapping.

        Returns:
            Dictionary containing stored variables and an 'env' dictionary for OS env.
        """
        context = dict(self._store)
        context["env"] = dict(os.environ)
        return context

    def _replace_env_placeholders(self, text: str) -> str:
        """Replace ${VAR} and ${VAR:-default} shell-style syntax with values.

        Args:
            text: Input string with potential ${VAR} references.

        Returns:
            String with replaced environment references.
        """
        pattern = re.compile(r"\$\{([A-Za-z0-9_]+)(?::-([^}]*))?\}")

        def replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            default_val = match.group(2) if match.group(2) is not None else ""
            val = self._store.get(var_name, os.environ.get(var_name))
            if val is not None:
                return str(val)
            return default_val

        return pattern.sub(replacer, text)

    def render(self, value: Any) -> Any:
        """Recursively render template expressions in strings, dicts, and lists.

        Preserves native types when single template expression evaluates to non-string.

        Args:
            value: Data structure or scalar to render.

        Returns:
            Rendered value with variables substituted.
        """
        if isinstance(value, str):
            processed = self._replace_env_placeholders(value)
            if "{{" in processed or "{%" in processed:
                try:
                    template = self._env.from_string(processed)
                    context = self.all_variables()
                    return template.render(**context)
                except Exception as exc:
                    raise VariableError(
                        f"Failed to render template expression '{processed}': {exc}"
                    ) from exc
            return processed
        if hasattr(value, "model_dump") and hasattr(value, "model_validate"):
            dumped = value.model_dump()
            rendered_dump = self.render(dumped)
            return type(value).model_validate(rendered_dump)
        if isinstance(value, dict):
            return {
                (str(self.render(k)) if isinstance(k, str) else k): self.render(v)
                for k, v in value.items()
            }
        if isinstance(value, list):
            return [self.render(item) for item in value]
        if isinstance(value, tuple):
            return tuple(self.render(item) for item in value)
        return value

    def extract(
        self,
        source: str,
        expression: str,
        response: HttpResponseData,
        default: Any = None,
    ) -> Any:
        """Extract a value from an HTTP response based on source and expression.

        Args:
            source: Extraction source ('jsonpath', 'header', 'regex', 'body', 'status_code').
            expression: Extraction pattern (path, header name, regex).
            response: Executed HTTP response data.
            default: Fallback value if extraction fails.

        Returns:
            Extracted value.

        Raises:
            VariableExtractionError: If extraction fails and no default is provided.
        """
        try:
            if source == "jsonpath":
                if response.body is None:
                    if default is not None:
                        return default
                    raise VariableExtractionError("Response body is empty, cannot run JSONPath")
                parser = parse_jsonpath(expression)
                matches = parser.find(response.body)
                if not matches:
                    if default is not None:
                        return default
                    raise VariableExtractionError(
                        f"JSONPath '{expression}' found no matches in response body"
                    )
                return matches[0].value

            if source == "header":
                header_name = expression.lower()
                for key, val in response.headers.items():
                    if key.lower() == header_name:
                        return val
                if default is not None:
                    return default
                raise VariableExtractionError(
                    f"Header '{expression}' not found in response headers"
                )

            if source == "regex":
                match = re.search(expression, response.text)
                if match:
                    if match.groups():
                        return match.group(1)
                    return match.group(0)
                if default is not None:
                    return default
                raise VariableExtractionError(
                    f"Regex '{expression}' did not match response body text"
                )

            if source == "status_code":
                return response.status_code

            if source == "body":
                return response.body if response.body is not None else response.text

            raise VariableExtractionError(f"Unsupported extraction source: '{source}'")

        except VariableExtractionError:
            raise
        except Exception as exc:
            if default is not None:
                return default
            raise VariableExtractionError(
                f"Failed extracting '{expression}' from {source}: {exc}"
            ) from exc
