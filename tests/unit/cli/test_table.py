# SPDX-License-Identifier: Apache-2.0
"""Tests of the table of commands and of the import-light check."""

import sys
import types
import typing
from pathlib import Path
from typing import TYPE_CHECKING

from wio.cli.table import COMMANDS, Component, component_entry

if TYPE_CHECKING:
    from argparse import Namespace

    import pytest

    from wio.cli.ports import Command, CommandSpec
    from wio.io.ports import Stdio

SRC = Path(__file__).resolve().parents[3] / "src" / "wio"
NOT_COMPONENTS = {"cli", "env", "errors", "formats", "io", "models", "ports"}


class _Spec:
    """A command spec that the stand-in component describes."""

    name = "stand-in"
    help = "A stand-in."

    def configure(self, parser: object) -> None:
        """Add nothing.

        Args:
            parser: Ignored.
        """


class _Command:
    """A command that the test never runs."""

    def run(self, args: Namespace, stdio: Stdio) -> int:
        """Return success.

        Args:
            args: Ignored.
            stdio: Ignored.

        Returns:
            0.
        """
        del args, stdio
        return 0


def test_describing_an_entry_does_not_wire_it(monkeypatch: pytest.MonkeyPatch) -> None:
    """The `describe` of a `component_entry` returns the spec and wires nothing."""
    # Given a stand-in module installed as wio.config whose describe() returns a
    # spec, and an entry from component_entry("config", wire)
    spec = _Spec()
    stand_in = types.SimpleNamespace(describe=lambda: spec)
    monkeypatch.setitem(sys.modules, "wio.config", stand_in)
    wired: list[str] = []

    def wire() -> Command:
        wired.append("config")
        return _Command()

    entry = component_entry("config", wire)

    # When the entry's describe() is called
    described: CommandSpec = entry.describe()

    # Then it returns that spec and wire was not called
    assert described is spec
    assert wired == []


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
