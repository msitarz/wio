# SPDX-License-Identifier: Apache-2.0
"""The check form of `wio trailers`, in its commit-time mode.

`wio trailers check --require [PATH]` judges a commit message against the config
and the Works it was written for, so that a wrong record is refused before it
enters the history. `wio.cli` dispatches on the first argument and wires the
ports, and this module holds what the form does, so it is run in a test with
fakes. The later check of a body or a range, `wio.trailers.later`, shares the form and
is chosen when `--require` is absent. The records are read and their form is
judged by `wio.formats`, and their fields by the validator of this package.
"""

from typing import TYPE_CHECKING, Final

from wio.formats import check_shape, read
from wio.models.diagnostics import Diagnostic
from wio.trailers.errors import TrailersError
from wio.trailers.later import run_later
from wio.trailers.report import (
    by_line,
    read_message,
    record_fields,
    record_lines,
    shape_diagnostics,
    write_diagnostics,
)
from wio.trailers.validation import validate_record

_EXEMPT: Final = ("Merge ", "Revert ", "Reapply ", "fixup! ", "squash! ")
"""The starts of the subjects that git writes, each with the space that follows."""

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from wio.io.ports import Stdio
    from wio.models.config import Config
    from wio.models.records import Finding, Reading
    from wio.trailers import Services
    from wio.trailers.ports import Contracts

_ERRORS: Final = frozenset({"malformed", "invisible"})
"""The kinds of finding that refuse a commit message; `unknown-key` only warns."""


def has_exempt_subject(message: str) -> bool:
    """Tell whether git wrote the subject of a message, which needs no record.

    The subject is the first line that is not a `#` comment, because a commit-msg
    hook sees the comments that git removes afterwards. It is exempt when it starts
    with `Merge`, `Revert`, `Reapply`, `fixup!` or `squash!` followed by a space, so
    `amend! x`, `fixup!x` and `Merged x` are not. The exemption is only from the
    requirement of a record: a record that such a message has is still judged.

    A blank first line that is not a comment is the subject, so the message is not
    exempt.

    Args:
        message: The commit message as the hook is given it.

    Returns:
        Whether the subject is one that git writes. A message with no subject, such
        as an empty one, has none.
    """
    subject = next((line for line in message.splitlines() if line[:1] != "#"), None)
    return subject is not None and subject.startswith(_EXEMPT)


def check_commit_message(
    message: str, contracts: Contracts, config: Config
) -> list[Diagnostic]:
    """Judge a commit message as it is committed.

    The records are read with the reader of the config and judged in three steps.
    `check_shape` judges each record's own form: a `malformed` or `invisible` finding
    is an error, and an `unknown-key` finding is a warning, deliberately, because a
    key that the engine no longer defines is no reason to refuse a commit. A finding
    belongs to the record whose lines hold its `number`, and an `invisible` finding
    belongs to no record, since its lines are not read as one. Every record that has
    no `malformed` finding is then judged by `validate_record` against the config and
    the Works, with the fields carrying their lines in the message, so a record with
    only an `unknown-key` warning is validated too, and a name that the config lacks,
    a Work or an item that does not exist and a result that does not fit its stage
    are errors, and a stage outside the Work's pipeline is a warning. A record that
    is malformed is not validated, because its fields cannot be trusted, and a
    `Wio-Work: none` record has nothing to check. Last, a message that has no record,
    which is a reading with no record, whatever its findings, and whose subject is
    not one that git writes, has the error `no record was found` at line 1. A message
    with no subject, such as an empty one or one of comments, is not exempt.

    The order is a local sort and not `sort_diagnostics`, which compares `where` as
    text, so that line 10 follows line 9.

    Args:
        message: The commit message.
        contracts: Finds the Works in the index and then in `HEAD`, so that a Work
            that the commit being made deletes is still found.
        config: The config, for the reader, the names and the results.

    Returns:
        The diagnostics, each with the 1-based line number in the message as its
        `where`, or `1` for the record that was not found, sorted by that number as
        a number, then errors before warnings, then by message. This is the check of
        the commit-time mode only: the later check judges the same findings with other
        severities, so `run_check` dispatches on the mode.
    """
    reader = config.trailers.reader
    reading, findings = read(message, reader), check_shape(message, reader)
    found = [
        *shape_diagnostics(findings, _ERRORS),
        *_record_diagnostics(reading, findings, (contracts, config)),
        *_missing_record(message, reading),
    ]
    return sorted(found, key=by_line)


def configure_check(parser: ArgumentParser) -> None:
    """Add the arguments of the check form to its parser.

    It does no I/O. `path` is optional: the file that holds the message or the body,
    or standard input when it is `-` or absent. `--require` selects the commit-time
    mode, which requires a record, and `--ref-range` selects the later check of the
    commits of a range, which is a provisional name as the parent's third assumption
    says. Neither is given for the later check of a body.

    Args:
        parser: The parser that `wio.cli` created for `check`.
    """
    parser.add_argument("path", nargs="?", help="The file with the message, or -.")
    parser.add_argument(
        "--require",
        action="store_true",
        help="Judge a commit message, which needs a record unless git wrote it.",
    )
    parser.add_argument(
        "--ref-range",
        help="Check the commits of a git revision range, such as main..HEAD.",
    )


def run_check(services: Services, args: Namespace, stdio: Stdio) -> int:
    """Check the commit message, the body or the range of the arguments.

    With `--require` the commit-time mode judges the commit message that is read from
    the file or from standard input, and otherwise the later check judges a body or,
    with `--ref-range`, the commits of a range, which `run_later` does. Each
    diagnostic is written to standard error as `<severity>: <where>: <message>`, one
    to a line, in its order, and nothing is written to standard output.

    Args:
        services: The ports the form reads the config, the message and the Works
            through.
        args: The arguments that `configure_check` parsed.
        stdio: Where the message is read when it is not in a file and where the
            diagnostics are written.

    Returns:
        1 when a diagnostic is an error, and otherwise 0, so a warning never changes
        the exit code.

    Raises:
        TrailersError: If `--require` is given with `--ref-range`, which is not a
            call of any mode, or if the file cannot be read or decoded.
        ConfigurationError: If the config cannot be read.
    """
    if not args.require:
        return run_later(services, args, stdio)
    if args.ref_range is not None:
        message = "--require checks one commit message and cannot be given --ref-range."
        raise TrailersError(message)
    config = services.settings.load()
    message = read_message(services, args.path, stdio)
    diagnostics = check_commit_message(message, services.staged_contracts, config)
    return write_diagnostics(diagnostics, stdio)


def _record_diagnostics(
    reading: Reading, findings: list[Finding], judge: tuple[Contracts, Config]
) -> list[Diagnostic]:
    """Judge the fields of the records that are not malformed."""
    contracts, config = judge
    malformed = {f.number for f in findings if f.kind == "malformed"}
    sound = [r for r in reading.records if record_lines(r).isdisjoint(malformed)]
    return [
        diagnostic
        for record in sound
        for diagnostic in validate_record(record_fields(record), contracts, config)
    ]


def _missing_record(message: str, reading: Reading) -> list[Diagnostic]:
    """Require a record of a message whose subject is not one that git writes."""
    if reading.records or has_exempt_subject(message):
        return []
    return [Diagnostic("error", "1", "no record was found")]
