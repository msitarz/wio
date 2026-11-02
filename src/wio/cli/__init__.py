# SPDX-License-Identifier: Apache-2.0
"""Command-line entry points for wio."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.io.ports import Stdio


def hello() -> str:
    """Return a greeting.

    Returns:
        The string `"world"`.
    """
    return "world"


def main(argv: Sequence[str], stdio: Stdio) -> int:
    """Run `wio` with the given arguments and streams.

    This is the testable core of the command: it reads and writes only through
    `stdio`, so a test can give it in-memory streams. Until the Work of the
    `cli` package decides what `wio` does, it succeeds without output.

    Args:
        argv: The arguments after the program name.
        stdio: The standard streams to use.

    Returns:
        The exit code: 0 on success, 1 when a check fails, and 2 for a usage or
        configuration error.
    """
    raise NotImplementedError


def console_main() -> int:
    """Run `wio` as the installed console script does.

    It builds the adapter for the process's standard streams and runs `main`
    with the arguments after the program name.

    Returns:
        The exit code of `main`.
    """
    raise NotImplementedError
