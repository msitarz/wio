# SPDX-License-Identifier: Apache-2.0
"""The ports that `wio.cli` consumes: the two halves of a component's command.

A command is split so that describing it needs no wiring: `wio.cli` builds the
whole usage from the `CommandSpec` of every command on every run, and wires a
`Command` only for the one that was chosen. Provisional: the members may change
when the first component adds its command.
"""

from argparse import ArgumentParser, Namespace
from typing import Protocol

from wio.io.ports import Stdio

class CommandSpec(Protocol):
    """What the usage needs to know about one `wio` subcommand.

    A component's `describe()` returns it. Making and using it does no I/O and
    raises nothing in a working installation, because it happens for every
    command on every run.
    """

    @property
    def name(self) -> str:
        """The subcommand's name, as typed after `wio`."""
        ...

    @property
    def help(self) -> str:
        """One line that `wio --help` shows for the subcommand."""
        ...

    def configure(self, parser: ArgumentParser) -> None:
        """Add the subcommand's arguments, `--json` among them, to its subparser.

        It does no I/O and raises nothing in a working installation, because it
        runs for every command on every run.

        Args:
            parser: The subparser that `wio.cli` created for the subcommand.
        """
        ...

class Command(Protocol):
    """The object that runs one `wio` subcommand once it has been chosen."""

    def run(self, args: Namespace, stdio: Stdio) -> int:
        """Run the subcommand.

        Args:
            args: The parsed arguments.
            stdio: The streams to read and write; the command never uses `sys`.

        Returns:
            The exit code: 0 on success, 1 when a check fails, and 2 for a
            usage or configuration error.
        """
        ...
