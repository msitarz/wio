# SPDX-License-Identifier: Apache-2.0
"""The table of commands: one entry per subcommand of a component.

Provisional: the names `table` and `COMMANDS` may change; `Component`, `Entry`
and `component_entry` are required as written.
"""

import importlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Literal

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from wio.cli.ports import Command, CommandSpec

type Component = Literal[
    "config", "contracts", "templates", "rules", "trailers", "log", "context"
]
"""The components of wio, so the type checker rejects any other package name."""


@dataclass(frozen=True)
class Entry:
    """One subcommand: how to describe it and how to wire it, kept apart."""

    package: Component
    """The component whose package provides the command."""

    describe: Callable[[], CommandSpec]
    """Describe the command without wiring it or loading its implementation.

    It does no I/O and raises nothing in a working installation, because it
    runs for every entry on every run.
    """

    wire: Callable[[], Command]
    """Build the command with the adapters its component needs.

    It runs once, and only when the subcommand was chosen.
    """


def component_entry(package: Component, wire: Callable[[], Command]) -> Entry:
    """Make the entry of a component's command.

    The entry's `describe` imports `wio.<package>` and returns its `describe()`,
    a function every component's package provides. It does no I/O and raises
    nothing in a working installation.

    Args:
        package: The component, a name the type checker restricts.
        wire: Builds the command when its subcommand is chosen.

    Returns:
        The entry for the table.
    """

    def describe() -> CommandSpec:
        """Import the component's package and describe its command.

        Returns:
            The command spec the package's `describe()` returns.
        """
        spec: CommandSpec = importlib.import_module(f"wio.{package}").describe()
        return spec

    return Entry(package=package, describe=describe, wire=wire)


COMMANDS: Final[Sequence[Entry]] = ()
"""Every subcommand of wio, empty until a component adds its entry."""
