# SPDX-License-Identifier: Apache-2.0
"""The type of a finding, shared by every `check` command."""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Iterable

type Severity = Literal["error", "warning", "note"]


@dataclass(frozen=True)
class Diagnostic:
    """One finding of a check: how serious, where and what.

    It is immutable, and `where` is a plain string, such as a key path.

    Attributes:
        severity: How serious the finding is.
        where: The place of the finding, compared as a plain string.
        message: What is wrong or worth knowing.
    """

    severity: Severity
    where: str
    message: str


_RANK: dict[Severity, int] = {"error": 0, "warning": 1, "note": 2}
_FILE_PLACE = re.compile(
    r"^(?P<file>[^,]*\.md)(?::(?P<line>\d+))?(?::(?P<column>\d+))?$"
)
"""A place that is a file, with the line and the column that may follow it."""


def _key(diagnostic: Diagnostic) -> tuple[str, int, str]:
    """Give the sort key of a diagnostic.

    Args:
        diagnostic: The finding.

    Returns:
        Its place, the rank of its severity and its message.
    """
    return (diagnostic.where, _RANK[diagnostic.severity], diagnostic.message)


def sort_diagnostics(diagnostics: Iterable[Diagnostic]) -> tuple[Diagnostic, ...]:
    """Put diagnostics in the one order every renderer prints them.

    Args:
        diagnostics: The findings, in any order.

    Returns:
        The findings sorted by `where`, then error, warning and note, then
        `message`, as plain strings (so `x[10]` sorts before `x[2]`).
    """
    return tuple(sorted(diagnostics, key=_key))


def order_diagnostics(diagnostics: Iterable[Diagnostic]) -> tuple[Diagnostic, ...]:
    """Put diagnostics in the order that a check of files prints them.

    It is not `sort_diagnostics`, which compares `where` as a plain string, and
    it keeps the rank of severities that this module already holds.

    Args:
        diagnostics: The findings, in any order.

    Returns:
        The findings by file, then by line and column as numbers, so that line 4
        precedes line 12. A `where` is read as a file with an optional line and
        an optional column, and a file alone precedes its lines. Any other
        `where`, such as a key path or two files joined by `, `, is compared as
        text and follows every place that is a file. Equal places are ordered by
        error, warning and note, then by message.
    """
    ordered = sorted(diagnostics, key=_order_key)
    return tuple(ordered)


def _order_key(diagnostic: Diagnostic) -> tuple[bool, str, int, int, int, str]:
    """Give the key by which a check of files orders a diagnostic.

    Args:
        diagnostic: The finding.

    Returns:
        Whether its place is not a file, the file or the text of the place, the
        line and the column as numbers, then the rank of the severity and the
        message.
    """
    match = _FILE_PLACE.match(diagnostic.where)
    place: tuple[str, int, int] = (
        (match["file"], int(match["line"] or 0), int(match["column"] or 0))
        if match
        else (diagnostic.where, 0, 0)
    )
    file, line, column = place
    rank = _RANK[diagnostic.severity]
    return (match is None, file, line, column, rank, diagnostic.message)


def has_error(diagnostics: Iterable[Diagnostic]) -> bool:
    """Tell whether a diagnostic is an error, which is what fails a check.

    Args:
        diagnostics: The findings of a check.

    Returns:
        Whether any of them is an error; a warning or a note is not.
    """
    return any(diagnostic.severity == "error" for diagnostic in diagnostics)
