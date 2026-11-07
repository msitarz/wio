# SPDX-License-Identifier: Apache-2.0
"""Tests that the table of commands and the packages of `src/wio` agree."""

import typing
from pathlib import Path

from wio.cli.table import COMMANDS, Component

SRC = Path(__file__).resolve().parents[2] / "src" / "wio"
NOT_COMPONENTS = {"cli", "env", "errors", "formats", "io", "models", "ports"}


def test_the_component_names_match_the_packages() -> None:
    """`Component` names exactly the packages that are components."""
    # Given the packages directly under src/wio and the packages that are not
    # components, which this test lists
    packages = {
        path.stem
        for path in SRC.iterdir()
        if path.name != "__pycache__" and path.suffix in {"", ".py", ".pyi"}
    } - {"__init__"}

    # When the first without the second is compared to the names in Component
    # (read from Component.__value__, because Component is a `type` alias)
    names = set(typing.get_args(Component.__value__))

    # Then the two are equal
    assert packages - NOT_COMPONENTS == names


def test_every_entry_of_the_real_table_names_a_component() -> None:
    """Each entry of the real table has a package that `Component` names."""
    # Given the real table of commands

    # When each entry's package is read
    packages = {entry.package for entry in COMMANDS}

    # Then each is a name in Component
    assert packages <= set(typing.get_args(Component.__value__))
