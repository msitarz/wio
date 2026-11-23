# SPDX-License-Identifier: Apache-2.0
"""The `wio rules` command: its group of subcommands."""

from typing import TYPE_CHECKING

from wio.rules import SUBCOMMANDS

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Sequence

    from wio.io.ports import Stdio
    from wio.rules import Services, Subcommand


class RulesCommand:
    """The object that `wio.cli` runs for `wio rules`."""

    def __init__(
        self, services: Services, table: Sequence[Subcommand] = SUBCOMMANDS
    ) -> None:
        """Remember the services and the entries to choose from.

        Args:
            services: Handed to the handler of the chosen entry.
            table: The entries; the package's own table unless a test passes
                another.
        """
        self._table = tuple(table)
        self._services = services

    def run(self, args: Namespace, stdio: Stdio) -> int:
        """Hand over to the chosen subcommand, or print the usage.

        Args:
            args: The parsed arguments, with `rules_subcommand` holding the name
                that was typed, or `None`, and `rules_help` giving the usage.
            stdio: The streams to write to.

        Returns:
            What the handler returned, or 0 after the usage. With no
            subcommand it reads no config and no file, so it works in any
            directory.

        Raises:
            WioError: The handler raised it for a mistake the user must fix; it
                reaches the command line, which exits 2.
        """
        del args, stdio
        raise NotImplementedError
