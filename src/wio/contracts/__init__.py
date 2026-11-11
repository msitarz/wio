# SPDX-License-Identifier: Apache-2.0
"""The `wio contracts` command: creating, checking and showing Work contracts."""

from typing import TYPE_CHECKING

from wio.contracts.table import SUBCOMMANDS, Services, Subcommand
lazy from wio.contracts.command import ContractsCommand
lazy from wio.contracts.errors import ContractsError

if TYPE_CHECKING:
    from argparse import ArgumentParser
    from collections.abc import Sequence


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
