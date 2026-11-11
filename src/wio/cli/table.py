# SPDX-License-Identifier: Apache-2.0
"""The table of commands: one entry per subcommand of a component.

Provisional: the names `table` and `COMMANDS` may change; `Component`, `Entry`
and `component_entry` are required as written.
"""

import importlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Literal

lazy from wio.config import ConfigCommand, ConfigSettings
lazy from wio.contracts import ContractsCommand, Services
lazy from wio.env import adapters as env
lazy from wio.io import adapters as io
lazy from wio.templates import TemplatesCatalog, TemplatesCommand

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


def _config() -> Command:
    """Wire `wio config` to the local disk and the git repository.

    Returns:
        The command, reading the config file through the adapters.
    """
    repository = io.GitRepository(env.ProcessEnvironment())
    return ConfigCommand(repository, io.LocalFileSystem())


def _templates() -> Command:
    """Wire `wio templates` to the local disk, the git repository and the config.

    Returns:
        The command, finding the templates through the adapters.
    """
    repository = io.GitRepository(env.ProcessEnvironment())
    files = io.LocalFileSystem()
    return TemplatesCommand(ConfigSettings(repository, files), repository, files)


def _contracts() -> Command:
    """Wire `wio contracts` to the disk, the repository, the config and the templates.

    Returns:
        The command, whose subcommands read the project through the adapters and
        find the templates through the catalog of `wio.templates`.
    """
    repository = io.GitRepository(env.ProcessEnvironment())
    files = io.LocalFileSystem()
    settings = ConfigSettings(repository, files)
    catalog = TemplatesCatalog(settings, repository, files)
    return ContractsCommand(Services(settings, repository, files, catalog))


COMMANDS: Final[Sequence[Entry]] = (
    component_entry("config", _config),
    component_entry("contracts", _contracts),
    component_entry("templates", _templates),
)
"""Every subcommand of wio, one entry for each component that has a command."""
