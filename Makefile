.PHONY: install lint format type-check test clean all build help

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

install: ## Create venv and install dependencies
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

lint: ## Run linter
	$(PYTHON) -m ruff check src/ tests/
	$(PYTHON) -m ruff format --check src/ tests/

format: ## Auto-format code
	$(PYTHON) -m ruff format src/ tests/
	$(PYTHON) -m ruff check --fix src/ tests/

type-check: ## Run type checker
	$(PYTHON) -m mypy src/

test: ## Run tests with coverage
	$(PYTHON) -m pytest

build: ## Build sdist and wheel packages for PyPI
	$(PYTHON) -m pip install --upgrade build
	$(PYTHON) -m build

clean: ## Remove caches and build artifacts
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml dist/ build/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +

all: lint type-check test ## Run all verification checks

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
