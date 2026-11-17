# SPDX-License-Identifier: Apache-2.0
"""The reader and the shape check of the `Wio-*` records of a commit message.

The stub is the spec until the implementation stage of the Work that builds the
record parser replaces it with a `.py` of the same annotations and docstrings.
Every `wio trailers` command reads records through `read` and judges their form
through `check_shape`, so no command has its own idea of either.
"""

from typing import Literal

from wio.models.records import Finding, Reading

def read(message: str, reader: Literal["scan", "git"]) -> Reading:
    """Read the records of a message the way the configured reader does.

    The `scan` reader takes every paragraph made only of `Wio-` lines, outside
    fenced code blocks and not after a `#`; the `git` reader takes only the
    trailers of the last paragraph, as `git interpret-trailers` does. A `Wio-`
    line that the reader does not take is kept as rejected, never dropped.

    Args:
        message: The whole commit message, or a pull request body.
        reader: The reader the project configured.

    Returns:
        The records in the order of the message, and the rejected `Wio-` lines.
        It judges no form: a record with a wrong value is still a record.
    """
    ...

def check_shape(message: str, reader: Literal["scan", "git"]) -> list[Finding]:
    """Judge the form of every record of a message.

    A record is judged for its keys, the form of each value and the ids of each
    list, and not against the config or the Works, which the modes check. A
    rejected `Wio-` line is an `invisible` finding.

    Args:
        message: The whole commit message, or a pull request body.
        reader: The reader the project configured.

    Returns:
        The findings in the order of the message, none for a valid message, one
        for a message with no record. Never raises for a message.
    """
    ...
