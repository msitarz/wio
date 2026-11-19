# SPDX-License-Identifier: Apache-2.0
"""The versioned JSON line format of the event log."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.models.events import Envelope, Event


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
    raise NotImplementedError


def decode_lines(text: str) -> Decoding:
    """Read supported entries and count unreadable nonblank lines.

    Args:
        text: JSON lines that can contain entries of different event types.

    Returns:
        The decoded entries in line order and the number of rejected lines.
        Blank lines and unknown fields on supported entries are ignored.
    """
    raise NotImplementedError
