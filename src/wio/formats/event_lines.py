# SPDX-License-Identifier: Apache-2.0
"""The versioned JSON line format of the event log."""

import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast
lazy import json

from wio.formats.diagnostics import encode_json
from wio.models.events import ContextEvent, Envelope, ReviewEvent
from wio.models.frozen import freeze

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.models.events import Event

_VERSION = 1
_UTC_TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?(?:[Zz]|[+-]00:00)"
)


@dataclass(frozen=True)
class Entry:
    """One decoded event and its recording context.

    Attributes:
        envelope: The common recording context.
        event: The fields of the context or review event.
    """

    envelope: Envelope
    event: Event


@dataclass(frozen=True)
class Decoding:
    """The usable entries and skipped lines of one log input.

    Attributes:
        entries: Successfully decoded entries in input order.
        skipped: The number of nonblank lines that could not be decoded.
    """

    entries: tuple[Entry, ...]
    skipped: int


def encode_line(envelope: Envelope, event: Event) -> str:
    """Encode an event as a version 1 JSON object and a terminating newline.

    Args:
        envelope: The recording context, with a finite, nonnegative UTC time.
        event: The context or review event to record.

    Returns:
        A single line of JSON. The UTC timestamp has millisecond precision,
        truncated after rounding to the microsecond. Absent optional fields
        are omitted, and required fields are included even when empty.

    Raises:
        ValueError: The envelope time is negative, nonfinite or outside the
            supported UTC date range.
    """
    kind = "context" if isinstance(event, ContextEvent) else "review"
    fields = {"v": _VERSION, "type": kind, **_envelope_fields(envelope)}
    return encode_json(fields | _event_fields(event)) + "\n"


def decode_lines(text: str) -> Decoding:
    """Read supported entries and count unreadable nonblank lines.

    Args:
        text: JSON lines that can contain entries of different event types.

    Returns:
        The decoded entries in line order and the number of rejected lines.
        Blank lines and unknown fields on supported entries are ignored.
    """
    entries: list[Entry] = []
    skipped = 0
    for line in text.split("\n"):
        if not line.strip():
            continue
        entry = _decode_entry(line)
        if entry is None:
            skipped += 1
        else:
            entries.append(entry)
    return Decoding(tuple(entries), skipped)


def _envelope_fields(envelope: Envelope) -> dict[str, object]:
    """Project the shared recording context onto its wire fields.

    Args:
        envelope: The recording context with a valid time.

    Returns:
        The time, directory and applicable optional fields.
    """
    fields: dict[str, object] = {
        "time": _format_time(envelope.time),
        "directory": envelope.directory,
        **_present(
            harness=envelope.harness, session=envelope.session, parent=envelope.parent
        ),
    }
    if envelope.matches:
        fields["matches"] = envelope.matches
    if envelope.ids:
        fields["ids"] = dict(envelope.ids)
    return fields


def _event_fields(event: Event) -> dict[str, object]:
    """Project the fields specific to one event onto the wire object.

    Args:
        event: The context or review event being encoded.

    Returns:
        The event's required fields and any applicable optional fields.
    """
    shared: dict[str, object] = {
        "work": event.work,
        "action": event.action,
        "stage": event.stage,
    }
    if isinstance(event, ContextEvent):
        return shared | {
            "bundle": event.bundle,
            "size": event.size,
            "rules": dict(event.rules),
            **_present(start=event.start, dirty=event.dirty),
        }
    return shared | {
        "commit": event.commit,
        "judge": event.judge,
        "result": event.result,
        "cited": dict(event.cited),
        "hashes": dict(event.hashes),
    }


def _present(**fields: object) -> dict[str, object]:
    """Keep explicitly supplied optional values, including false and empty strings.

    Args:
        **fields: Wire fields whose absence is represented by `None`.

    Returns:
        The fields whose values are present.
    """
    return {name: value for name, value in fields.items() if value is not None}


def _format_time(seconds: float) -> str:
    """Write Unix time in UTC to the millisecond after microsecond rounding.

    Args:
        seconds: The envelope time in seconds since the epoch.

    Returns:
        A UTC timestamp with three fractional digits and a trailing `Z`.

    Raises:
        ValueError: The time is negative, nonfinite or outside the UTC date range.
    """
    if not math.isfinite(seconds) or seconds < 0:
        message = "event time must be finite and nonnegative"
        raise ValueError(message)
    try:
        instant = datetime.fromtimestamp(seconds, UTC)
    except (OverflowError, OSError) as error:
        message = "event time is outside the supported UTC date range"
        raise ValueError(message) from error
    return instant.isoformat(timespec="milliseconds").removesuffix("+00:00") + "Z"


def _decode_entry(line: str) -> Entry | None:
    """Read one nonblank record without affecting its neighbors.

    Args:
        line: A nonblank line of event log text.

    Returns:
        The decoded entry, or `None` when the line cannot be read.
    """
    try:
        fields = json.loads(
            line, parse_int=_read_integer, parse_constant=_reject_constant
        )
        return _read_fields(fields)
    except ValueError, RecursionError:
        return None


def _read_integer(token: str) -> int | None:
    """Convert a JSON integer under Python's integer conversion limit.

    Args:
        token: A syntactically valid JSON integer token.

    Returns:
        The integer or `None` when conversion exceeds the limit. Integer
        fields reject that marker. Unknown fields remain ignorable.
    """
    try:
        return int(token)
    except ValueError:
        return None


def _reject_constant(_token: str) -> None:
    """Refuse a nonfinite number token outside the JSON grammar.

    Args:
        _token: The nonstandard token passed by the JSON parser.

    Raises:
        ValueError: Always, so the line reader skips the malformed object.
    """
    raise ValueError


def _read_fields(value: object) -> Entry:
    """Build a typed entry from a decoded JSON value.

    Args:
        value: The decoded value, before validation.

    Returns:
        The entry represented by a supported object.

    Raises:
        ValueError: The value is malformed or its version or event type is
            unsupported.
    """
    if not isinstance(value, dict) or _field(value, "v", int) != _VERSION:
        raise ValueError
    return Entry(_read_envelope(value), _read_event(value))


def _read_envelope(row: Mapping[str, object]) -> Envelope:
    """Read a version 1 envelope and restore omitted optional fields.

    Args:
        row: The event log object, including its envelope fields.

    Returns:
        The recorded time, directory and session details.

    Raises:
        ValueError: A supplied field or required value is invalid.
    """
    return Envelope(
        time=_read_time(_field(row, "time", str)),
        directory=_field(row, "directory", str),
        harness=_optional(row, "harness", str),
        session=_optional(row, "session", str),
        parent=_optional(row, "parent", str),
        matches=_matches(row) if "matches" in row else (),
        ids=_strings_by_name(row, "ids") if "ids" in row else frozendict(),
    )


def _read_event(row: Mapping[str, object]) -> Event:
    """Select and read the payload of a supported event type.

    Args:
        row: The event log object with its event tag and fields.

    Returns:
        The context or review payload.

    Raises:
        ValueError: The event type is unknown or a payload field is invalid.
    """
    work = _field(row, "work", str)
    action = _field(row, "action", str)
    stage = _field(row, "stage", str)
    match row.get("type"):
        case "context":
            return ContextEvent(
                work=work,
                action=action,
                stage=stage,
                bundle=_field(row, "bundle", str),
                size=_field(row, "size", int),
                rules=_strings_by_name(row, "rules"),
                start=_optional(row, "start", str),
                dirty=_optional(row, "dirty", bool),
            )
        case "review":
            return ReviewEvent(
                work=work,
                action=action,
                stage=stage,
                commit=_field(row, "commit", str),
                judge=_field(row, "judge", str),
                result=_field(row, "result", str),
                cited=_strings_by_name(row, "cited"),
                hashes=_strings_by_name(row, "hashes"),
            )
        case _:
            raise ValueError


def _read_time(value: str) -> float:
    """Read a UTC timestamp representable as nonnegative Unix time.

    Args:
        value: The timestamp from the event log object.

    Returns:
        Seconds since the Unix epoch in UTC.

    Raises:
        ValueError: The text is outside the UTC timestamp grammar or cannot be
            represented as nonnegative Unix time.
    """
    if not _UTC_TIMESTAMP.fullmatch(value):
        raise ValueError
    seconds = datetime.fromisoformat(value.upper()).timestamp()
    if seconds < 0:
        raise ValueError
    return seconds


def _field[T](row: Mapping[str, object], name: str, kind: type[T]) -> T:
    """Require an exact wire type, with booleans distinct from integers.

    Args:
        row: The event log object.
        name: The field to read.
        kind: Its expected type after JSON parsing.

    Returns:
        The supplied value with the requested type.

    Raises:
        ValueError: The field is missing or has the wrong type.
    """
    value = row.get(name)
    if type(value) is not kind:
        raise ValueError
    return cast("T", value)


def _optional[T](row: Mapping[str, object], name: str, kind: type[T]) -> T | None:
    """Read a field whose absence is represented by omission.

    Args:
        row: The event log object.
        name: The optional field to read.
        kind: Its type when supplied.

    Returns:
        The supplied value, or `None` for an absent field.

    Raises:
        ValueError: The field is present with the wrong type.
    """
    return _field(row, name, kind) if name in row else None


def _strings_by_name(row: Mapping[str, object], name: str) -> frozendict[str, str]:
    """Read a JSON object as an ordered, immutable string mapping.

    Args:
        row: The event log object.
        name: The field holding the mapping.

    Returns:
        The mapping with its key order preserved.

    Raises:
        ValueError: The field is missing, not an object or has a nonstring value.
    """
    mapping: dict[str, object] = _field(row, name, dict)
    if any(not isinstance(value, str) for value in mapping.values()):
        raise ValueError
    return freeze(cast("dict[str, str]", mapping))


def _matches(row: Mapping[str, object]) -> tuple[str, ...]:
    """Read the harness matches in their recorded order.

    Args:
        row: The event log object containing a matches field.

    Returns:
        The matching harness names in input order.

    Raises:
        ValueError: The field is not an array or contains a nonstring value.
    """
    values: list[object] = _field(row, "matches", list)
    if any(not isinstance(value, str) for value in values):
        raise ValueError
    return tuple(cast("list[str]", values))
