# api-test-framework

[![CI](https://github.com/CHUKEPC/api-test-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/CHUKEPC/api-test-framework/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type Checked: mypy](https://img.shields.io/badge/mypy-strict-blue.svg)](https://mypy-lang.org/)

A declarative REST API testing framework with YAML DSL, native pytest plugin integration, JSONPath assertions, variable chaining, authentication helpers, and rich reporting. PyPI-ready Python package.

---

## Features

- **Declarative YAML & JSON DSL**: Define complete HTTP API test suites with minimal boilerplate.
- **Pytest Plugin Integration**: Automatically discover and execute `test_*.yaml` test files through native `pytest` runner (`pytest11` entry-point).
- **Variable Chaining**: Extract response data (via JSONPath, headers, regex) in step $N$ and inject into step $N+1$ dynamically.
- **Jinja2 Templating & Dynamic Variables**: Native templating expressions (`{{ uuid() }}`, `{{ timestamp() }}`, `{{ random_int(1, 100) }}`) and shell-style environment substitution (`${API_URL:-http://localhost}`).
- **Rich Assertion Engine**:
  - HTTP Status Codes (exact code or acceptable list `[200, 201]`)
  - Deep JSON Body subset comparison
  - JSONPath expressions (`jsonpath-ng`) with operators: `equals`, `not_equals`, `contains`, `exists`, `regex`, `gt`, `gte`, `lt`, `lte`, `type`, `len`
  - JSON Schema validation (`Draft 2020-12`)
  - Header inspection (case-insensitive with `equals`, `contains`, `regex`, `exists`)
  - Response duration and performance thresholds (`max_duration`)
  - Custom assertion function registry
- **Async HTTP Client**: High-performance HTTP client backed by `httpx` with configurable retries, delays, SSL verification, and timeout policies.
- **Authentication Helpers**: Built-in support for Bearer tokens, HTTP Basic Auth, API Keys (header or query param), and OAuth2 Client Credentials flow.
- **Suite Lifecycle Hooks**: Declarative `setup` and `teardown` requests executed before and after test suites.
- **Comprehensive Reporting**:
  - Rich ANSI terminal summaries with tables and color-coded status badges
  - Interactive self-contained HTML reports
  - Standard JUnit XML reports for CI/CD pipeline integration
  - Machine-readable structured JSON reports
- **Standalone CLI**: Run tests, validate YAML syntax, and scaffold new test suites with `api-test`.

---

## Architecture

Following clean architectural boundaries with dedicated sub-packages:

```
src/api_test_framework/
├── __init__.py
├── main.py              # CLI entry point
├── config.py            # Runtime configuration (timeouts, retries, base URLs)
├── exceptions.py        # Framework exception hierarchy
├── py.typed             # PEP 561 typing marker
├── pytest_plugin.py     # pytest plugin (discovery, collector, items, fixtures)
├── variables.py         # Jinja2 template rendering and response extraction
├── loader/              # Test suite file loading and schema validation
│   ├── __init__.py
│   ├── json_loader.py
│   ├── validator.py
│   └── yaml_loader.py
├── models/              # Pydantic domain models
│   ├── __init__.py
│   ├── assertion.py
│   ├── request.py
│   ├── response.py
│   ├── result.py
│   ├── test_case.py
│   └── test_suite.py
├── runner/              # Execution engine
│   ├── __init__.py
│   ├── chain.py         # Sequential runner with variable chaining & hooks
│   ├── executor.py      # Async httpx client with retry policy
│   └── parallel.py      # Bounded concurrency parallel runner
├── assertions/          # Modular assertion engines
│   ├── __init__.py
│   ├── body.py          # Deep comparison, regex, substring
│   ├── headers.py       # Header assertions
│   ├── jsonpath.py      # jsonpath-ng query checks
│   ├── registry.py      # Custom assertion function hooks
│   ├── schema.py        # JSON Schema validation
│   ├── status.py        # Status code checking
│   └── timing.py        # Max latency assertions
├── auth/                # Authentication strategies
│   ├── __init__.py
│   ├── api_key.py       # API Key (header/query)
│   ├── base.py          # Abstract BaseAuth
│   ├── basic.py         # HTTP Basic Auth (base64)
│   ├── bearer.py        # Bearer token auth
│   └── oauth2.py        # OAuth2 client credentials flow
├── reporting/           # Report generators
│   ├── __init__.py
│   ├── base.py          # Abstract BaseReporter
│   ├── html.py          # HTML report generator
│   ├── json_report.py   # JSON report generator
│   ├── junit.py         # JUnit XML generator
│   └── terminal.py      # Rich terminal reporter
└── cli/                 # Click CLI commands
    ├── __init__.py
    ├── app.py           # run, validate, init commands
    └── template.py      # Scaffolding template
```

---

## Installation

```bash
# Install from source or local checkout
pip install -e .

# With development and test dependencies
pip install -e ".[dev]"
```

---

## Quick Start

### 1. Scaffold a New Test File

Generate a sample test file using the CLI:

```bash
api-test init test_users.yaml
```

### 2. Example YAML Test Definition

Here is a declarative test file demonstrating authentication, requests, assertions, and variable chaining:

```yaml
name: "Users API Verification Suite"
description: "Verify user creation, retrieval, and schema adherence"
base_url: "https://jsonplaceholder.typicode.com"

# Default headers for every request in suite
headers:
  Content-Type: "application/json"
  Accept: "application/json"

# Initial variables (supports built-in generators like uuid, timestamp)
variables:
  new_username: "qa_lead_{{ random_str(6) }}"
  new_email: "qa_{{ random_int(100, 999) }}@example.com"

tests:
  - name: "Create new user"
    description: "POST request creating a user and capturing generated ID"
    request:
      method: "POST"
      url: "/users"
      json:
        name: "Test Engineer"
        username: "{{ new_username }}"
        email: "{{ new_email }}"
    assertions:
      status_code: 201
      headers:
        content-type:
          op: "contains"
          expected: "application/json"
      jsonpath:
        - path: "$.id"
          op: "exists"
        - path: "$.username"
          op: "equals"
          expected: "{{ new_username }}"
      max_duration: 3.0
    extract:
      - name: "created_user_id"
        source: "jsonpath"
        expression: "$.id"

  - name: "Retrieve created user"
    description: "GET request referencing the captured created_user_id"
    request:
      method: "GET"
      url: "/users/1"  # Or /users/{{ created_user_id }}
    assertions:
      status_code: 200
      jsonpath:
        - path: "$.id"
          op: "equals"
          expected: 1
      max_duration: 2.0
```

### 3. Run with CLI

```bash
# Run test suite and print rich console output
api-test run test_users.yaml

# Run with HTML, JUnit XML, and JSON reports
api-test run test_users.yaml --report-html report.html --report-junit report.xml --report-json report.json

# Run all test files in a directory concurrently
api-test run examples/ --parallel --workers 4

# Validate YAML syntax and schema without executing requests
api-test validate test_users.yaml
```

### 4. Run with Pytest

The framework registers itself as a native `pytest11` plugin. Any file named `test_*.yaml` or `*_test.yaml` is discovered automatically:

```bash
# Run YAML tests through pytest
pytest examples/

# Pass CLI options to pytest
pytest examples/ --api-base-url="https://api.staging.example.com" --api-auth-token="secret-token"
```

Available pytest fixtures in tests:
- `api_client`: Pre-configured `HttpExecutor` instance
- `base_url`: Resolved base URL from options or environment
- `auth_token`: Resolved auth token
- `api_vars`: Fresh `VariableManager` store

---

## Assertions Reference

| Assertion Key | Description | Example |
| :--- | :--- | :--- |
| `status_code` | Exact code or list of allowed status codes | `status_code: 200` or `status_code: [200, 201]` |
| `headers` | Key-value pairs or list of rules (`equals`, `contains`, `regex`, `exists`) | `content-type: { op: "contains", expected: "application/json" }` |
| `body` | Exact body or deep subset comparison | `body: { "status": "ok" }` |
| `body_contains` | Substring required in response body text | `body_contains: "Success"` |
| `body_regex` | Regex pattern matching response body | `body_regex: "token=[A-Za-z0-9]+"` |
| `jsonpath` | List of JSONPath assertions with comparison operators | `- path: "$.data[0].id", op: "gt", expected: 0` |
| `schema` | JSON Schema dict or path to `.json` / `.yaml` schema file | `schema: "schemas/user.json"` |
| `max_duration` | Maximum response latency in seconds | `max_duration: 1.5` |
| `custom` | Custom registered assertion function names | `custom: ["check_csrf_token"]` |

### JSONPath Operators

- `equals`: Exact equality (`val == expected`)
- `not_equals`: Inequality check
- `contains`: Substring or item in list
- `exists`: Check if path exists (`expected: true` or `expected: false`)
- `regex`: Match against regular expression pattern
- `gt`, `gte`, `lt`, `lte`: Numeric comparisons
- `type`: Check type name (`str`, `int`, `float`, `bool`, `list`, `dict`)
- `len`: Check length of collection or string

---

## Authentication Reference

```yaml
# Bearer Token
auth:
  type: "bearer"
  token: "{{ auth_token }}"

# HTTP Basic Auth
auth:
  type: "basic"
  username: "admin"
  password: "password123"

# API Key in Header or Query Parameter
auth:
  type: "api_key"
  key_name: "X-API-Key"
  key_value: "secret-key-val"
  location: "header" # or "query"

# OAuth2 Client Credentials Flow
auth:
  type: "oauth2"
  token_url: "https://auth.example.com/oauth/token"
  client_id: "client-id"
  client_secret: "client-secret"
  scope: "read write"
```

---

## Development & Testing

```bash
# Run linting (ruff)
make lint

# Run type checker (mypy strict mode)
make type-check

# Run unit and integration tests with coverage
make test

# Build sdist and wheel distributions
make build
```

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
