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
# The wiring stage adds the package files; `cli` is already a package.
WAITING = pytest.mark.xfail(
    strict=True,
    raises=(AssertionError, ModuleNotFoundError),
    reason="the wiring stage adds the packages",
)


@pytest.mark.parametrize(
    "name",
    [pytest.param(n, marks=[] if n == "cli" else [WAITING]) for n in PACKAGES],
)
def test_every_package_imports_and_states_its_role(name: str) -> None:
    """A package of v0.1 imports, and its docstring is one sentence."""
    # Given a package of v0.1

    # When it is imported and its docstring read
    module = importlib.import_module(f"wio.{name}")
    doc = (module.__doc__ or "").strip()

    # Then the docstring is a single sentence
    assert doc.endswith(".")
    assert "\n" not in doc
    assert doc.count(". ") == 0
