# SPDX-License-Identifier: Apache-2.0
"""What the modes of the check form share: reading a message and reporting.

The commit-time check and the later check read a message the same way, write their
diagnostics the same way and order a message's diagnostics by line, so the helpers
live here and neither mode imports the other.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from wio.models.diagnostics import Diagnostic
from wio.trailers.errors import TrailersError
from wio.trailers.validation import Field

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.io.ports import Stdio
    from wio.models.records import Finding, Record
    from wio.trailers import Services


def read_message(services: Services, path: str | None, stdio: Stdio) -> str:
    """Read the commit message or the body to check.

    Args:
        services: The ports, of which `files` reads the file.
        path: The file, or `-` or `None` for standard input.
        stdio: Where standard input is read.

    Returns:
        The text of the message.

    Raises:
        TrailersError: If the file cannot be read or decoded.
    """
    if path is None or path == "-":
        return stdio.stdin.read()
    try:
        return services.files.read_text(Path(path))
    except (OSError, UnicodeDecodeError) as error:
        message = f"cannot read the message in {path}: {error}"
        raise TrailersError(message) from error


def by_line(diagnostic: Diagnostic) -> tuple[int, int, str]:
    """Give the key that orders the diagnostics of one message.

    Args:
        diagnostic: A diagnostic whose `where` is a line number.

    Returns:
        The line as a number, so that line 10 follows line 9, then 0 for an error and
        1 for a warning, then the message.
    """
    rank = 0 if diagnostic.severity == "error" else 1
    return (int(diagnostic.where), rank, diagnostic.message)


def write_diagnostics(diagnostics: Sequence[Diagnostic], stdio: Stdio) -> int:
    """Write the diagnostics of a check to standard error.

    Args:
        diagnostics: The diagnostics, in the order to write them.
        stdio: Where they are written.

    Returns:
        1 when a diagnostic is an error, and otherwise 0, so a warning never changes
        the exit code of a check.
    """
    for diagnostic in diagnostics:
        line = f"{diagnostic.severity}: {diagnostic.where}: {diagnostic.message}\n"
        stdio.stderr.write(line)
    return 1 if any(d.severity == "error" for d in diagnostics) else 0


def record_lines(record: Record) -> set[int]:
    """Give the lines that a record spans.

    Args:
        record: A record of the reading.

    Returns:
        The line number of each of its fields.
    """
    return {trailer.number for trailer in record.trailers}


def record_fields(record: Record) -> list[Field]:
    """Give the fields of a record, each with its line in the message.

    Args:
        record: A record of the reading.

    Returns:
        A field for each `Wio-` line, with the line number as its place.
    """
    return [Field(t.key, t.value, t.number) for t in record.trailers]


def shape_diagnostics(
    findings: Sequence[Finding], errors: frozenset[str]
) -> list[Diagnostic]:
    """Turn the findings of the shape check into diagnostics.

    Args:
        findings: What `check_shape` found.
        errors: The kinds of finding that are errors, where the mode decides this;
            every other kind is a warning.

    Returns:
        A diagnostic for each finding, at the line of the finding.
    """
    return [
        Diagnostic(
            "error" if finding.kind in errors else "warning",
            str(finding.number),
            finding.message,
        )
        for finding in findings
    ]
