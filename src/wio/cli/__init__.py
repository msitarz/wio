# SPDX-License-Identifier: Apache-2.0
"""Command-line entry points for wio."""

import sys
from typing import TYPE_CHECKING

from wio.cli.table import COMMANDS
lazy from wio.io import adapters

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.cli.table import Entry
    from wio.io.ports import Stdio


def main(
    argv: Sequence[str],
    stdio: Stdio,
    commands: Sequence[Entry] = COMMANDS,
) -> int:
    """Run `wio` with the given arguments and streams.

    This is the testable core of the command: it reads and writes only through
    `stdio`, so a test can give it in-memory streams. It describes every entry
    of `commands` to build the usage, wires only the entry whose subcommand was
    chosen, and returns that command's exit code. Bare `wio` and `--help` print
    the package's summary and the subcommands in order of name, `--version`
    prints `wio <version>`, and a usage mistake exits 2 with argparse's message
    on standard error. Until the dispatch is implemented, it succeeds without
    output.

    Args:
        argv: The arguments after the program name.
        stdio: The standard streams to use.
        commands: The entries of the subcommands, the table of commands by
            default.

    Returns:
        The exit code: 0 on success, 1 when a check fails, and 2 for a usage
        or configuration error.
    """
    del argv, stdio, commands
    return 0


def console_main() -> int:
    """Run `wio` as the installed console script does.

    It builds the adapter for the process's standard streams and runs `main`
    with the arguments after the program name.

    Returns:
        The exit code of `main`.
    """
    return main(sys.argv[1:], adapters.SystemStdio())
