# SPDX-License-Identifier: Apache-2.0
"""The dispatch of `wio` to the entries of the table of commands."""

import argparse
import contextlib
import importlib.metadata
import traceback
from typing import TYPE_CHECKING

from wio.errors import DiagnosticsError, WioError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.cli.table import Entry
    from wio.io.ports import Stdio

_DISTRIBUTION = "work-it-out"
_ENTRY = "wio_entry"
_NAME = "wio_command"
_CODES = (0, 1)


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
        subparser.set_defaults(**{_ENTRY: entry, _NAME: spec.name})
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


def _checked(name: str, code: int, stdio: Stdio) -> int:
    """Accept only the exit codes a command may return.

    Args:
        name: The subcommand that returned the code.
        code: The exit code it returned.
        stdio: The streams to report a wrong code to.

    Returns:
        The code itself when it is 0 or 1, and 70 after reporting a bug.
    """
    if code in _CODES:
        return code
    stdio.stderr.write(f"error: {name} returned exit code {code}, not 0 or 1\n")
    return 70


def _run(argv: Sequence[str], stdio: Stdio, commands: Sequence[Entry]) -> int:
    """Describe, parse, wire and run, letting any failure escape.

    Args:
        argv: The arguments after the program name.
        stdio: The standard streams to write the output to.
        commands: The entries of the subcommands.

    Returns:
        The exit code of the chosen command, or of the introduction.
    """
    parser = build_parser(commands)
    args = parse(parser, argv)
    if isinstance(args, int):
        return args
    entry: Entry | None = getattr(args, _ENTRY, None)
    if entry is None:
        parser.print_help()
        return 0
    code = entry.wire().run(args, stdio)
    return _checked(getattr(args, _NAME), code, stdio)


def _report(error: WioError) -> str:
    """Word a `WioError` for standard error.

    Args:
        error: What a step raised.

    Returns:
        `error: <message>`, except for an error that carries diagnostics, whose
        message is the diagnostics rendered one to a line with their own
        severity, so it is written as it is.
    """
    if isinstance(error, DiagnosticsError) and error.diagnostics:
        return str(error)
    return f"error: {error}"


def run(argv: Sequence[str], stdio: Stdio, commands: Sequence[Entry]) -> int:
    """Run the subcommand that `argv` chooses, or print the introduction.

    Everything is written to `stdio`. A `WioError` at any step is reported as
    `error:` and its message, or as its diagnostics when it carries them, and
    exits 2, and any other exception is reported with its traceback and exits
    70.

    Args:
        argv: The arguments after the program name.
        stdio: The standard streams to write the output to.
        commands: The entries of the subcommands.

    Returns:
        The exit code of the chosen command, or of the introduction, or 2 or 70
        for a failure.
    """
    with (
        contextlib.redirect_stdout(stdio.stdout),
        contextlib.redirect_stderr(stdio.stderr),
    ):
        try:
            return _run(argv, stdio, commands)
        except WioError as error:
            stdio.stderr.write(f"{_report(error)}\n")
            return 2
        except Exception:  # noqa: BLE001 - a bug in any step must exit 70
            traceback.print_exc(file=stdio.stderr)
            return 70
