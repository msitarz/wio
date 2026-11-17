# SPDX-License-Identifier: Apache-2.0
"""The types of a record as `wio.formats` reads it, and of a finding about it."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Trailer:
    """One `Wio-` line of a message.

    It is immutable. Provisional: the implementation stage may rename its
    fields.

    Attributes:
        key: The key as written, such as `Wio-Work`.
        value: The text after the colon, without the spaces around it.
        text: The whole line as written.
        number: The 1-based number of the line in the message.
    """

    key: str
    value: str
    text: str
    number: int


@dataclass(frozen=True)
class Record:
    """The `Wio-` lines of one paragraph that the configured reader reads.

    It is immutable. Provisional: the implementation stage may rename its
    fields.

    Attributes:
        trailers: The lines in the order of the paragraph, a repeated key
            included. It is never empty.
    """

    trailers: tuple[Trailer, ...]


@dataclass(frozen=True)
class Reading:
    """What the configured reader sees in a message.

    It is immutable. Provisional: the implementation stage may rename its
    fields.

    Attributes:
        records: The records in the order of the message.
        rejected: The `Wio-` lines that the reader does not take as part of a
            record, in the order of the message. A line in a fenced code block
            or after a `#` is not one, because no reader would take it.
    """

    records: tuple[Record, ...]
    rejected: tuple[Trailer, ...]


@dataclass(frozen=True)
class Finding:
    """One thing wrong with the records of a message.

    It carries no severity, which the mode that uses it decides. It is
    immutable. Provisional: the implementation stage may rename its fields.

    Attributes:
        kind: `malformed` for a record or a value that breaks its form,
            `unknown-key` for a `Wio-` key the engine does not define, and
            `invisible` for a `Wio-` line the configured reader cannot see.
        key: The key the finding is about, or `None` when it is about no key.
        line: The line as written. For a problem of a whole record, such as a
            missing key, the first line of the record.
        number: The 1-based number of `line` in the message.
        message: A non-empty sentence that says what is wrong.
    """

    kind: Literal["malformed", "unknown-key", "invisible"]
    key: str | None
    line: str
    number: int
    message: str
