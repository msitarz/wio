# SPDX-License-Identifier: Apache-2.0
"""The `wio contracts` command: creating, checking and showing Work contracts."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

lazy from wio.contracts.command import ContractsCommand
lazy from wio.contracts.errors import ContractsError

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from collections.abc import Callable, Sequence

    from wio.contracts.ports import TemplateCatalog
    from wio.io.ports import FileSystem, Repository, Stdio
    from wio.ports import Settings


@dataclass(frozen=True)
class Services:
    """What a subcommand reads the project through.

    Provisional: a leaf that needs another port, such as randomness, adds a field.

    Attributes:
        settings: Loads the config.
        repository: Finds the repository root.
        files: Lists and reads files.
        catalog: Finds the templates of the project.
    """

    settings: Settings
    repository: Repository
    files: FileSystem
    catalog: TemplateCatalog


@dataclass(frozen=True)
class Subcommand:
    """One subcommand of `wio contracts`, described and run apart.

    Provisional: the field names and the handler's signature may change, and the
    entry holds at least these four things.

    Attributes:
        name: The subcommand's name, as typed after `wio contracts`.
        help: One line that `wio contracts --help` shows for it.
        configure: Adds its arguments to its subparser. It does no I/O, because
            it runs on every run.
        handler: Runs it with the services, the parsed arguments and the
            streams, and returns the exit code: 0, or 1 for a failed check. A
            mistake the user must fix is a `ContractsError`, and not a code.
    """

    name: str
    help: str
    configure: Callable[[ArgumentParser], None]
    handler: Callable[[Services, Namespace, Stdio], int]


SUBCOMMANDS: Final[Sequence[Subcommand]] = ()
"""The subcommands of `wio contracts`, to which each leaf adds its own entry.

It lives here and not in a module of its own, because describing the command
loads no module of the package besides this one, and that holds for `configure`
as well, which runs when the command is described. So an entry's `configure` is
defined in this module, and its `handler` is a function of this module that
imports the leaf's own module when it runs. A `lazy from` in the tuple would
not defer anything, because the names are used as the tuple is built.
"""


class ContractsSpec:
    """What the usage needs to know about `wio contracts`, and nothing more."""

    name = "contracts"
    help = "Create, list, check and show the Work contracts of the project."

    def __init__(self, table: Sequence[Subcommand] = SUBCOMMANDS) -> None:
        """Keep the table that the subcommands are described from.

        Args:
            table: The subcommands, which defaults to the table of the package
                and which a test replaces.
        """
        self._table = table

    def configure(self, parser: ArgumentParser) -> None:
        """Add the subcommands of `wio contracts` to its subparser.

        It does no I/O and imports no codec, and sets the defaults
        `contracts_subcommand` (`None` for the bare command) and `contracts_help`
        (the usage), so that the bare command loads no config.

        Args:
            parser: The subparser that `wio.cli` created for `contracts`.
        """
        views = parser.add_subparsers(title="subcommands", metavar="<subcommand>")
        parser.set_defaults(
            contracts_subcommand=None, contracts_help=parser.format_help
        )
        for entry in self._table:
            subparser = views.add_parser(
                entry.name, help=entry.help, description=entry.help
            )
            subparser.set_defaults(contracts_subcommand=entry.name)
            entry.configure(subparser)


def describe(table: Sequence[Subcommand] = SUBCOMMANDS) -> ContractsSpec:
    """Describe `wio contracts` without loading its implementation.

    Args:
        table: The subcommands, which a test replaces.

    Returns:
        The command spec of `contracts`.
    """
    return ContractsSpec(table)


__all__ = [
    "SUBCOMMANDS",
    "ContractsCommand",
    "ContractsError",
    "ContractsSpec",
    "Services",
    "Subcommand",
    "describe",
]
