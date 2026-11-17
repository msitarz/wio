# SPDX-License-Identifier: Apache-2.0
"""The reader and the shape check of the `Wio-*` records of a commit message.

Every `wio trailers` command reads records through `read` and judges their form
through `check_shape`, so no command has its own idea of either. Both read a
message as text and touch no file, git or config.
"""

import re
from itertools import groupby
from operator import attrgetter
from typing import TYPE_CHECKING, Literal

from wio.models.records import Finding, Reading, Record, Trailer

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

    from wio.models.config import Reader

type _Block = list[tuple[int, str]]
"""A paragraph as its lines with their 1-based numbers in the message."""

_TRAILER = re.compile(r"(?P<key>[A-Za-z][A-Za-z0-9-]*):[ \t]*(?P<value>.*?)[ \t]*")
_FENCE = re.compile(r" {0,3}(```|~~~)")
_NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
_KNOWN = frozenset(
    ("Wio-Work", "Wio-Action", "Wio-Stage", "Wio-Items", "Wio-Result", "Wio-Judge")
)
_NEEDS_WORK = ("Wio-Action", "Wio-Stage")


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
    list, and not against the config or the Works, which the modes check. A key
    that is missing, repeated or forbidden in a `Wio-Work: none` record, a
    `Wio-Judge` with no `Wio-Result`, and a repeated id or a `none` in a list of
    Works are `malformed`; a `Wio-` key the engine does not define is
    `unknown-key`. A
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
    rejected = map(_invisible, reading.rejected)
    return sorted([*findings, *rejected], key=attrgetter("number"))


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
    blocks = _blocks(message, skip_quoted=not last_only)
    records: list[Record] = []
    rejected: list[Trailer] = []
    for index, block in enumerate(blocks):
        taken = not last_only or index == len(blocks) - 1
        record = _as_record(block) if taken else None
        if record is None:
            rejected.extend(_wio_lines(block))
        else:
            records.append(record)
    return Reading(tuple(records), tuple(rejected))


def _blocks(message: str, *, skip_quoted: bool) -> list[_Block]:
    """Cut a message into paragraphs at its blank lines.

    Args:
        message: The whole commit message.
        skip_quoted: Leave out the lines of fenced code blocks, which also end
            a paragraph, and the lines that start with `#`.

    Returns:
        The non-empty paragraphs, each with the numbers of its lines.
    """
    kept = _kept(message, skip_quoted=skip_quoted)
    return [
        [line for line in g if line] for cut, g in groupby(kept, key=_is_cut) if not cut
    ]


def _is_cut(line: tuple[int, str] | None) -> bool:
    """Tell whether an entry of `_kept` ends a paragraph.

    Args:
        line: An entry of `_kept`.

    Returns:
        True for the separator entry `None`.
    """
    return line is None


def _kept(message: str, *, skip_quoted: bool) -> Iterator[tuple[int, str] | None]:
    """Walk the lines of a message, marking where paragraphs end.

    Args:
        message: The whole commit message.
        skip_quoted: Drop the lines of fenced code blocks and the lines that
            start with `#`, and end a paragraph at each fence.

    Yields:
        `None` at a blank line or a fence, and each other kept line with its
        1-based number.
    """
    fenced = False
    for number, text in enumerate(message.splitlines(), start=1):
        opens = skip_quoted and _FENCE.match(text) is not None
        fenced = fenced != opens
        if opens or not text.strip():
            yield None
        elif not _dropped(text, fenced=fenced, skip_quoted=skip_quoted):
            yield number, text


def _dropped(text: str, *, fenced: bool, skip_quoted: bool) -> bool:
    """Tell whether the `scan` reader leaves a line out.

    Args:
        text: The line.
        fenced: Whether the line is inside a fenced code block.
        skip_quoted: Whether the reader leaves such lines out at all.

    Returns:
        True for a line in a fenced block or one that starts with `#`.
    """
    return skip_quoted and (fenced or text.startswith("#"))


def _parse(number: int, text: str) -> Trailer | None:
    """Read a line as a `Key: value` trailer.

    Args:
        number: The 1-based number of the line in the message.
        text: The line.

    Returns:
        The trailer, or `None` when the line is not one.
    """
    match = _TRAILER.fullmatch(text)
    if match is None:
        return None
    return Trailer(match["key"], match["value"], text, number)


def _wio_lines(block: _Block) -> tuple[Trailer, ...]:
    """Find the `Wio-` trailers among the lines of a paragraph.

    Args:
        block: A paragraph.

    Returns:
        The lines that are trailers with a `Wio-` key, in order.
    """
    parsed = (_parse(number, text) for number, text in block)
    return tuple(t for t in parsed if t is not None and t.key.startswith("Wio-"))


def _as_record(block: _Block) -> Record | None:
    """Take a paragraph as a record when every line is a trailer.

    Args:
        block: A paragraph.

    Returns:
        The record of its `Wio-` lines, or `None` when a line is not a trailer
        or no key starts with `Wio-`.
    """
    parsed = [_parse(number, text) for number, text in block]
    if any(t is None for t in parsed):
        return None
    wio = _wio_lines(block)
    return Record(wio) if wio else None


def _judge_record(record: Record) -> list[Finding]:
    """Judge the keys and the values of one record.

    Args:
        record: A record as the reader gave it.

    Returns:
        The `malformed` and `unknown-key` findings of the record, in the order
        of its lines.
    """
    unique, findings = _first_of_each(record.trailers)
    findings += [_unknown(t) for t in unique.values() if t.key not in _KNOWN]
    work = unique.get("Wio-Work")
    if work is not None and work.value == "none":
        return findings + _forbidden(unique)
    return findings + _bad_values(unique) + _missing(unique, record.trailers[0])


def _first_of_each(
    trailers: Iterable[Trailer],
) -> tuple[dict[str, Trailer], list[Finding]]:
    """Take the first trailer of each key and report the repeats.

    Args:
        trailers: The `Wio-` lines of a record.

    Returns:
        The first trailer of each key, and a `malformed` finding for each later
        one.
    """
    unique: dict[str, Trailer] = {}
    repeats: list[Finding] = []
    for trailer in trailers:
        if trailer.key in unique:
            repeats.append(_malformed(trailer, f"`{trailer.key}` is repeated."))
        else:
            unique[trailer.key] = trailer
    return unique, repeats


def _bad_values(unique: dict[str, Trailer]) -> list[Finding]:
    """Judge the form of the value of each known key.

    Args:
        unique: The first trailer of each key of a record.

    Returns:
        A `malformed` finding for each value of the wrong form.
    """
    found = []
    for key, trailer in unique.items():
        check = _VALUE_CHECKS.get(key)
        problem = check(trailer.value) if check else None
        if problem:
            found.append(_malformed(trailer, f"`{key}` {problem}."))
    return found


def _missing(unique: dict[str, Trailer], first: Trailer) -> list[Finding]:
    """Find the keys a record of a Work needs and does not have.

    Args:
        unique: The first trailer of each key of a record.
        first: The first line of the record, where a missing key is reported.

    Returns:
        A `malformed` finding for each missing `Wio-Work`, `Wio-Action` or
        `Wio-Stage`, and one for a `Wio-Judge` with no `Wio-Result`.
    """
    needed = ("Wio-Work", *(_NEEDS_WORK if "Wio-Work" in unique else ()))
    found = [
        _malformed(first, f"`{key}` is missing from the record.", key)
        for key in needed
        if key not in unique
    ]
    judge = unique.get("Wio-Judge")
    if judge is not None and "Wio-Result" not in unique:
        found.append(_malformed(judge, "`Wio-Judge` needs a `Wio-Result`."))
    return found


def _forbidden(unique: dict[str, Trailer]) -> list[Finding]:
    """Find the keys that a `Wio-Work: none` record must not have.

    Args:
        unique: The first trailer of each key of a record.

    Returns:
        A `malformed` finding for each key besides `Wio-Work`.
    """
    return [
        _malformed(t, f"`{t.key}` is not allowed in a `Wio-Work: none` record.")
        for key, t in unique.items()
        if key != "Wio-Work"
    ]


def _work_problem(value: str) -> str | None:
    """Judge the value of `Wio-Work`.

    Args:
        value: `none`, an id or ids separated by a comma and one space.

    Returns:
        What is wrong, or `None` when the value is fine.
    """
    if value == "none":
        return None
    ids = value.split(", ")
    if any(_bad_id(i) or i == "none" for i in ids):
        return "must be `none`, or ids without whitespace or commas"
    if len(set(ids)) != len(ids):
        return "lists an id twice"
    return None


def _bad_id(value: str) -> bool:
    """Tell whether a value is not an id.

    Args:
        value: A candidate id.

    Returns:
        True when it is empty or holds whitespace or a comma.
    """
    return not value or re.search(r"[\s,]", value) is not None


def _name_problem(value: str) -> str | None:
    """Judge a name: an action, a stage or a result.

    Args:
        value: The value.

    Returns:
        What is wrong, or `None` for lowercase letters, digits and hyphens that
        start with a letter or a digit.
    """
    ok = _NAME.fullmatch(value) is not None
    return None if ok else "must be lowercase letters, digits and hyphens"


def _items_problem(value: str) -> str | None:
    """Judge the value of `Wio-Items`.

    Args:
        value: Item ids separated by a comma and one space.

    Returns:
        What is wrong, or `None` when the value is fine.
    """
    if any(_bad_id(i) for i in value.split(", ")):
        return "must be ids separated by a comma and one space"
    return None


def _judge_problem(value: str) -> str | None:
    """Judge the value of `Wio-Judge`.

    Args:
        value: The value.

    Returns:
        What is wrong, or `None` for `human` or `agent`.
    """
    return None if value in {"human", "agent"} else "must be `human` or `agent`"


_VALUE_CHECKS: dict[str, Callable[[str], str | None]] = {
    "Wio-Work": _work_problem,
    "Wio-Action": _name_problem,
    "Wio-Stage": _name_problem,
    "Wio-Items": _items_problem,
    "Wio-Result": _name_problem,
    "Wio-Judge": _judge_problem,
}


def _finding(
    kind: Literal["malformed", "unknown-key", "invisible"],
    trailer: Trailer,
    message: str,
    key: str | None = None,
) -> Finding:
    """Make a finding at a line.

    Args:
        kind: The kind of finding.
        trailer: The line the finding is at.
        message: What is wrong, as a sentence.
        key: The key at fault, when it is not the line's own.

    Returns:
        The finding.
    """
    return Finding(kind, key or trailer.key, trailer.text, trailer.number, message)


def _malformed(trailer: Trailer, message: str, key: str | None = None) -> Finding:
    """Make a `malformed` finding at a line.

    Args:
        trailer: The line the finding is at.
        message: What is wrong, as a sentence.
        key: The key at fault, when it is not the line's own.

    Returns:
        The finding.
    """
    return _finding("malformed", trailer, message, key)


def _unknown(trailer: Trailer) -> Finding:
    """Make an `unknown-key` finding at a line.

    Args:
        trailer: The line with a `Wio-` key the engine does not define.

    Returns:
        The finding.
    """
    return _finding("unknown-key", trailer, f"`{trailer.key}` is not a key.")


def _invisible(line: Trailer) -> Finding:
    """Report a `Wio-` line that the reader rejected.

    Args:
        line: The rejected line.

    Returns:
        The `invisible` finding that says why no reader would see the line.
    """
    message = f"`{line.key}` is in no record that the configured reader reads."
    return _finding("invisible", line, message)
