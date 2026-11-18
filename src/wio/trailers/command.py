# SPDX-License-Identifier: Apache-2.0
"""The `wio trailers` command: the group of its four forms.

`wio trailers` runs the write form, `check`, `fold` and `none` from its arguments,
so a person or an agent reaches them as one command that tells them apart and
reports a usage mistake the same way for every form. The first argument chooses
the form: the word `check`, `fold` or `none` selects that subcommand, and any other
value is the Work of the write form, so a Work cannot be named `check`, `fold` or
`none`. An option before the first argument is a usage error. The group takes the
arguments after `trailers` as they are and parses them with the parser of the
chosen form, `configure_write`, `configure_check`, `configure_fold` or
`configure_nowork`, whose own mistakes, and a call with no
argument at all, raise a `TrailersError` that `wio.cli` turns into the exit code 2.
It has no `--json` option on purpose: the write form prints a plain record to append
to a commit message and a check sends its findings to standard error.

A mistake inside a form's own parser must not escape as a `SystemExit`, which
`wio.cli` does not handle. The group parses the forms with an `ArgumentParser`
subclass whose `error` raises a `TrailersError` with argparse's message, and whose
`exit` raises a private stop that `run` catches, so that a form's `-h` prints that
form's usage to standard output and the command exits 0. `configure_fold` builds its
nested subparsers with the class of its parent, so the subclass reaches them.
"""

import contextlib
from argparse import ArgumentParser
from dataclasses import dataclass
from typing import TYPE_CHECKING, NoReturn, override

from wio.trailers.check import configure_check, run_check
from wio.trailers.errors import TrailersError
from wio.trailers.fold import configure_fold, run_fold
from wio.trailers.nowork import configure_nowork, run_nowork
from wio.trailers.write import configure_write, run_write

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Callable, Sequence

    type _Runner = Callable[[Services, Namespace, Stdio], int]

    from wio.io.ports import Stdio
    from wio.trailers import Services


class _Stop(Exception):  # noqa: N818 - a private signal, not an error
    """Raised by a form's parser to end the parse after its usage was written."""


class _FormParser(ArgumentParser):
    """The parser of a form, which refuses and stops with exceptions, not exits.

    `wio.cli` handles a `WioError` and a returned exit code and nothing else, so a
    `SystemExit` of argparse inside a command would escape it.
    """

    @override
    def error(self, message: str) -> NoReturn:
        """Refuse the arguments.

        Args:
            message: What argparse found wrong.

        Raises:
            TrailersError: Always, with the message, which exits 2.
        """
        raise TrailersError(message)

    @override
    def exit(self, status: int = 0, message: str | None = None) -> NoReturn:
        """End the parse, as argparse does after a usage that `-h` asked for.

        Args:
            status: The exit status argparse asks for, which is ignored.
            message: What argparse would print, which is ignored.

        Raises:
            _Stop: Always, which `_parse` catches.
        """
        del status, message
        raise _Stop


@dataclass(frozen=True)
class TrailersCommand:
    """Runs `wio trailers`: the form that its first argument chooses.

    Attributes:
        services: The ports that the forms read the project through, wired by
            `wio.cli`.
    """

    services: Services

    def run(self, args: Namespace, stdio: Stdio) -> int:
        """Run the form that the arguments choose.

        `check` runs the check form and `fold` the fold form, each with the parser
        of its own `configure_*`, and any other first argument runs the write form
        with the arguments from that Work on. The exit code is the form's, 0 for
        what it printed or passed and 1 for a record or a message that does not
        hold, and 0 after the usage of a form that `-h` asked for. A call with no
        argument, an unknown option, a form with a missing or unknown argument and
        a form's own parse error are usage mistakes, written as `error: <message>`
        to standard error, with nothing on standard output; an option before the
        first argument is refused by the parser of `wio trailers` itself.

        Args:
            args: What the parser read, of which `forms` holds the arguments after
                `trailers`.
            stdio: Where the forms read and write.

        Returns:
            The exit code of the form: 0, or 1 for a failed check.

        Raises:
            TrailersError: For a usage mistake of any form, which exits 2.
            ConfigurationError: If a form loads a config that has an error.
        """
        forms: list[str] = args.forms
        if not forms:
            message = "name a Work, an action and a stage, or `check` or `fold`."
            raise TrailersError(message)
        name = forms[0]
        configure, runner = _FORMS.get(name, (configure_write, run_write))
        known = name in _FORMS
        prog = f"wio trailers {name}" if known else "wio trailers"
        parsed = _parse(configure, forms[1:] if known else forms, stdio, prog)
        return 0 if parsed is None else runner(self.services, parsed, stdio)


_FORMS: dict[str, tuple[Callable[[ArgumentParser], None], _Runner]] = {
    "check": (configure_check, run_check),
    "fold": (configure_fold, run_fold),
    "none": (configure_nowork, run_nowork),
}
"""The forms that a first argument names, with how each is configured and run; any
other first argument is the Work of the write form."""


def _parse(
    configure: Callable[[ArgumentParser], None],
    arguments: Sequence[str],
    stdio: Stdio,
    prog: str,
) -> Namespace | None:
    """Parse the arguments of one form with the parser that the form configures.

    Args:
        configure: The `configure_*` of the form, which adds its arguments.
        arguments: The arguments of the form, after its name for `check` and `fold`
            and from the Work on for the write form.
        stdio: Where the usage is written when `-h` asks for it.
        prog: The name that the usage gives the form, such as `wio trailers check`.

    Returns:
        The parsed arguments, or `None` after the usage of the form was written
        because `-h` asked for it.

    Raises:
        TrailersError: With argparse's message, for any mistake in the arguments.
    """
    parser = _FormParser(prog=prog)
    configure(parser)
    try:
        with contextlib.redirect_stdout(stdio.stdout):
            return parser.parse_args(list(arguments))
    except _Stop:
        return None
