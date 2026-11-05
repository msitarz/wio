# SPDX-License-Identifier: Apache-2.0
"""The dispatch of `wio` to the entries of the table of commands."""

import argparse
import contextlib
import importlib.metadata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.cli.table import Entry
    from wio.io.ports import Stdio

_DISTRIBUTION = "work-it-out"
_ENTRY = "wio_entry"


def build_parser(commands: Sequence[Entry]) -> argparse.ArgumentParser:
    """Build the parser of `wio`, with one subparser for each entry.

    Every entry is described, in order of name, and none is wired.

    Args:
        commands: The entries of the subcommands.

    Returns:
        The parser, whose parsed arguments carry the chosen entry, if any.
    """
    parser = argparse.ArgumentParser(
        prog="wio",
        description=importlib.metadata.metadata(_DISTRIBUTION)["Summary"],
    )
    version = importlib.metadata.version(_DISTRIBUTION)
    parser.add_argument("--version", action="version", version=f"wio {version}")
    subparsers = parser.add_subparsers(title="subcommands", metavar="<subcommand>")
    for entry, spec in sorted(
        ((entry, entry.describe()) for entry in commands), key=lambda pair: pair[1].name
    ):
        subparser = subparsers.add_parser(
            spec.name, help=spec.help, description=spec.help
        )
        spec.configure(subparser)
        subparser.set_defaults(**{_ENTRY: entry})
    return parser


def _exit_code(code: object) -> int:
    """Read the code of a `SystemExit`.

    Args:
        code: The `code` attribute of the exit.

    Returns:
        The code itself when it is an integer, 0 when there is none, and 1 for
        a message, which the interpreter treats as a failure.
    """
    match code:
        case None:
            return 0
        case int():
            return code
        case _:
            return 1


def parse(
    parser: argparse.ArgumentParser, argv: Sequence[str]
) -> argparse.Namespace | int:
    """Parse the arguments, turning argparse's exits into an exit code.

    Args:
        parser: The parser of `wio`.
        argv: The arguments after the program name.

    Returns:
        The parsed arguments, or the exit code when argparse exited: 0 after the
        help or the version, and 2 for a usage mistake.
    """
    try:
        return parser.parse_args(argv)
    except SystemExit as stop:
        return _exit_code(stop.code)


def run(argv: Sequence[str], stdio: Stdio, commands: Sequence[Entry]) -> int:
    """Run the subcommand that `argv` chooses, or print the introduction.

    Args:
        argv: The arguments after the program name.
        stdio: The standard streams to write the output to.
        commands: The entries of the subcommands.

    Returns:
        The exit code of the chosen command, or of the introduction.
    """
    with (
        contextlib.redirect_stdout(stdio.stdout),
        contextlib.redirect_stderr(stdio.stderr),
    ):
        parser = build_parser(commands)
        args = parse(parser, argv)
        if isinstance(args, int):
            return args
        entry: Entry | None = getattr(args, _ENTRY, None)
        if entry is None:
            parser.print_help()
            return 0
        return entry.wire().run(args, stdio)
