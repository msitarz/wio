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
_FILE_PLACE = re.compile(r"^[^,]+\.(?:md|toml)(?::\d+){0,2}$")
_DIGITS = re.compile(r"(\d+)")


def _natural_parts(text: str) -> tuple[tuple[int, int | str], ...]:
    """Split text into comparable text and integer chunks."""
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part)
        for part in _DIGITS.split(text)
        if part
    )


def _is_single_path(where: str) -> bool:
    """Return whether `where` names a single file or directory path."""
    if ", " in where:
        return False
    return "/" in where or _FILE_PLACE.match(where) is not None


def _order_key(
    diagnostic: Diagnostic,
) -> tuple[bool, tuple[tuple[int, int | str], ...], int, str]:
    """Give the natural sort key of a diagnostic."""
    return (
        not _is_single_path(diagnostic.where),
        _natural_parts(diagnostic.where),
        _RANK[diagnostic.severity],
        diagnostic.message,
    )


def sort_diagnostics(diagnostics: Iterable[Diagnostic]) -> tuple[Diagnostic, ...]:
    """Put diagnostics in the one natural order every renderer prints them.

    Numbers in `where` compare numerically (`file:4` before `file:12`, `x[2]`
    before `x[10]`). Equal places sort by error, warning, note, then message.
    """
    return tuple(sorted(diagnostics, key=_order_key))


def order_diagnostics(diagnostics: Iterable[Diagnostic]) -> tuple[Diagnostic, ...]:
    """Alias for `sort_diagnostics`."""
    return sort_diagnostics(diagnostics)


def has_error(diagnostics: Iterable[Diagnostic]) -> bool:
    """Tell whether a diagnostic is an error, which is what fails a check.

    Args:
        diagnostics: The findings of a check.

    Returns:
        Whether any of them is an error; a warning or a note is not.
    """
    return any(diagnostic.severity == "error" for diagnostic in diagnostics)
