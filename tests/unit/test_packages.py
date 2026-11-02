# SPDX-License-Identifier: Apache-2.0
"""Tests that every package of v0.1 exists and states its role."""

import importlib

import pytest

PACKAGES = (
    "models",
    "formats",
    "io",
    "config",
    "contract",
    "rule",
    "trailers",
    "log",
    "context",
    "cli",
)


@pytest.mark.parametrize("name", PACKAGES)
def test_every_package_imports_and_states_its_role(name: str) -> None:
    """A package of v0.1 imports, and its docstring is one sentence."""
    # Given a package of v0.1

    # When it is imported and its docstring read, with line wraps joined
    module = importlib.import_module(f"wio.{name}")
    doc = " ".join((module.__doc__ or "").split())

    # Then the docstring is a single sentence
    assert doc.endswith(".")
    assert doc.count(". ") == 0
