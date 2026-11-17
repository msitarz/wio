# SPDX-License-Identifier: Apache-2.0
"""The type for a commit as `wio.io.ports.History` reports it."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Commit:
    """A commit's full id and its message.

    The id lets a reader name the exact commit that a gate reviewed or that a
    session started from, and the message carries the records. It is immutable.

    Attributes:
        id: The full hash of the commit, 40 hexadecimal digits.
        message: The full message as git stores it, subject, body and trailer
            paragraph, without its trailing newline.
    """

    id: str
    message: str
