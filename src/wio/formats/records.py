# SPDX-License-Identifier: Apache-2.0
"""The reader and the shape check of the `Wio-*` records of a commit message.

Every `wio trailers` command reads records through `read` and judges their form
through `check_shape`, so no command has its own idea of either. The skeleton
composes them, and the leaves that do the work are stubbed.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.models.config import Reader
    from wio.models.records import Finding, Reading, Record, Trailer


def read(message: str, reader: Reader) -> Reading:
    """Read the records of a message the way the configured reader does.

    The `scan` reader takes every paragraph made only of `Wio-` lines, outside
    fenced code blocks and leaving out lines that start with `#`; the `git`
    reader takes only the trailers of the last paragraph, as
    `git interpret-trailers` does. A `Wio-` line that the reader would take for
    a record but does not, such as one in a paragraph with prose, is kept as
    rejected. Under `scan`, a line in a fenced code block or starting with `#`
    is none of the reader's business and is not rejected.

    Args:
        message: The whole commit message, or a pull request body.
        reader: The reader the project configured.

    Returns:
        The records in the order of the message, and the rejected `Wio-` lines.
        It judges no form: a record with a wrong value is still a record.
    """
    match reader:
        case "scan":
            return _paragraphs(message, last_only=False)
        case "git":
            return _paragraphs(message, last_only=True)


def check_shape(message: str, reader: Reader) -> list[Finding]:
    """Judge the form of every record of a message.

    A record is judged for its keys, the form of each value and the ids of each
    list, and not against the config or the Works, which the modes check. A
    rejected `Wio-` line is an `invisible` finding.

    Args:
        message: The whole commit message, or a pull request body.
        reader: The reader the project configured.

    Returns:
        The findings in the order of the message; none for a valid message and
        none for a message with no record, which a mode requires or not.
    """
    reading = read(message, reader)
    findings = [f for record in reading.records for f in _judge_record(record)]
    return [*findings, *map(_invisible, reading.rejected)]


def _paragraphs(message: str, *, last_only: bool) -> Reading:
    """Split a message into paragraphs and take its records from them.

    Args:
        message: The whole commit message, or a pull request body.
        last_only: Take only the trailers of the last paragraph, as the `git`
            reader does, instead of every paragraph made only of `Wio-` lines,
            outside fenced code blocks, as the `scan` reader does.

    Returns:
        The records, and the `Wio-` lines the reader would take for a record
        but does not.
    """
    raise NotImplementedError


def _judge_record(record: Record) -> list[Finding]:
    """Judge the keys and the values of one record.

    Args:
        record: A record as the reader gave it.

    Returns:
        The `malformed` and `unknown-key` findings of the record, in the order
        of its lines.
    """
    raise NotImplementedError


def _invisible(line: Trailer) -> Finding:
    """Report a `Wio-` line that the reader rejected.

    Args:
        line: The rejected line.

    Returns:
        The `invisible` finding that says why no reader would see the line.
    """
    raise NotImplementedError
