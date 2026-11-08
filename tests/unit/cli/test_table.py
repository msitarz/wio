# SPDX-License-Identifier: Apache-2.0
"""Tests of the table of commands and of the import-light check."""

import sys
import types
from pathlib import Path
from typing import TYPE_CHECKING

from wio.cli.table import component_entry

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
    # Given a stand-in for the config component that describes a spec, and an
    # entry that would wire it
    spec = _Spec()
    stand_in = types.SimpleNamespace(describe=lambda: spec)
    monkeypatch.setitem(sys.modules, "wio.config", stand_in)
    wired: list[str] = []

    def wire() -> Command:
        wired.append("config")
        return _Command()

    entry = component_entry("config", wire)

    # When the entry is described
    described: CommandSpec = entry.describe()

    # Then it returns that spec and wire was not called
    assert described is spec
    assert wired == []
