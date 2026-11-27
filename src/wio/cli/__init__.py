# SPDX-License-Identifier: Apache-2.0
"""Command-line entry points for wio."""

import sys
from typing import TYPE_CHECKING

from wio.cli.dispatch import run
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
    """Run `wio` with the given arguments and streams."""
    return run(argv, stdio, commands)


def console_main() -> int:
    """Run `wio` as the installed console script does.

    It builds the adapter for the process's standard streams and runs `main`
    with the arguments after the program name.

    Returns:
        The exit code of `main`.
    """
    return main(sys.argv[1:], adapters.SystemStdio())
