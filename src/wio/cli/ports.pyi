# SPDX-License-Identifier: Apache-2.0
"""The port that `wio.cli` consumes: a command of a component.

Provisional: the members may change when the first component adds its command.
`wio.cli` binds each command with a lazy import, so one invocation loads only
the command it runs.
"""

from argparse import ArgumentParser, Namespace
from typing import Protocol

from wio.io.ports import Stdio

class Command(Protocol):
    """The object a component exposes for one `wio` subcommand."""

    @property
    def name(self) -> str:
        """The subcommand's name, as typed after `wio`."""
        ...

    @property
    def help(self) -> str:
        """One line that `wio --help` shows for the subcommand."""
        ...

    def configure(self, parser: ArgumentParser) -> None:
        """Add the subcommand's arguments to its argparse subparser.

        Args:
            parser: The subparser that `wio.cli` created for the subcommand.
        """
        ...

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
