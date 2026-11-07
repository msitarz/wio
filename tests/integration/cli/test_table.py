# SPDX-License-Identifier: Apache-2.0
"""Tests of the import-light check on packages that a fresh interpreter imports."""

import pytest

from tests.support import import_light_violations
from wio.cli.table import COMMANDS

FIXTURES = "tests.integration.cli.fixtures"


@pytest.mark.slow
def test_import_light_violations_names_an_eager_import() -> None:
    """The check names the implementation that an eager package loads."""
    # Given two fixture packages, one whose __init__ imports an implementation
    # module eagerly and one that imports it lazily, each with a describe
    heavy, light = f"{FIXTURES}.heavy", f"{FIXTURES}.light"

    # When import_light_violations runs for each
    found = import_light_violations(heavy), import_light_violations(light)

    # Then it returns the implementation module for the first and an empty list
    # for the second
    assert found == ([f"{heavy}.impl"], [])


@pytest.mark.slow
def test_every_entry_of_the_real_table_is_import_light() -> None:
    """Describing a real command loads none of its implementation."""
    # Given the real table of commands

    # When import_light_violations runs for "wio." + entry.package of each
    found = [import_light_violations(f"wio.{entry.package}") for entry in COMMANDS]

    # Then each returns an empty list
    assert all(violations == [] for violations in found)
