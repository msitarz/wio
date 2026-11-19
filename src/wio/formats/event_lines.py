# SPDX-License-Identifier: Apache-2.0
"""The versioned JSON line format of the event log."""

from dataclasses import dataclass
from typing import TYPE_CHECKING
lazy import json

from wio.formats.diagnostics import encode_json
from wio.models.events import ContextEvent

if TYPE_CHECKING:
    from wio.models.events import Envelope, Event

_VERSION = 1


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
    return {"directory": envelope.directory}


def _event_fields(_event: Event) -> dict[str, object]:
    """Project the fields specific to one event onto the wire object.

    Args:
        _event: The context or review event being encoded.

    Returns:
        The event's required fields and any applicable optional fields.
    """
    return {}


def _decode_entry(line: str) -> Entry | None:
    """Read one nonblank record without affecting its neighbors.

    Args:
        line: A nonblank line of event log text.

    Returns:
        The decoded entry, or `None` when the line cannot be read.
    """
    try:
        return _read_fields(json.loads(line))
    except ValueError, RecursionError:
        return None


def _read_fields(_value: object) -> Entry:
    """Build a typed entry from a decoded JSON value.

    Args:
        _value: The decoded value, before validation.

    Returns:
        The entry represented by a supported object.

    Raises:
        ValueError: The value is malformed or its version or event type is
            unsupported.
    """
    raise ValueError
