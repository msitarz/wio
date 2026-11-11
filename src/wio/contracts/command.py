# SPDX-License-Identifier: Apache-2.0
"""The `wio contracts` command: its group of subcommands."""

from typing import TYPE_CHECKING

from wio.contracts.table import SUBCOMMANDS

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Sequence

    from wio.contracts.table import Services, Subcommand
    from wio.io.ports import Stdio


class ContractsCommand:
    """Runs `wio contracts`: its help and the subcommand that the table names."""

    def __init__(
        self, services: Services, table: Sequence[Subcommand] = SUBCOMMANDS
    ) -> None:
        """Keep what the group runs its subcommands with.

        Args:
            services: What a subcommand reads the project through.
            table: The subcommands, which defaults to the table of the package
                and which a test replaces.
        """
        self._services = services
        self._table = table

    def run(self, args: Namespace, stdio: Stdio) -> int:
        """Run the subcommand that the arguments chose, or write the help.

        Args:
            args: What the parser read: `contracts_subcommand`, the name of the
                chosen entry or `None` for bare `wio contracts`, and
                `contracts_help`, which returns the usage.
            stdio: Where the output and the errors go.

        Returns:
            The exit code of the subcommand, or 0 after the help. Bare
            `wio contracts` writes its help and reads no config and no file of
            the project, so it works anywhere.

        Raises:
            ContractsError: A subcommand raised it for what the user must fix; it
                is not caught here, and the command line exits 2.
            ConfigurationError: A subcommand loaded a config that has an error.
        """
        name: str | None = args.contracts_subcommand
        if name is None:
            stdio.stdout.write(args.contracts_help())
            return 0
        entry = {entry.name: entry for entry in self._table}[name]
        return entry.handler(self._services, args, stdio)
