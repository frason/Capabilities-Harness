"""Shared pytest configuration and fixtures."""

from __future__ import annotations

import pathlib

import pytest


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp(tmp_path: pathlib.Path) -> pathlib.Path:
    """Alias for pytest's built-in ``tmp_path`` fixture.

    Provides a temporary directory unique to the test invocation.
    The directory is automatically removed after the test session ends.
    """
    return tmp_path
