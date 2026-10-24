"""Tests for top-level main module entry point."""

from __future__ import annotations

import runpy
from unittest.mock import patch


def test_main_entrypoint() -> None:
    """Verify running api_test_framework.main calls cli."""
    with patch("api_test_framework.cli.app.cli") as mock_cli:
        runpy.run_module("api_test_framework.main", run_name="__main__")
        mock_cli.assert_called_once()
