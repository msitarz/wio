# SPDX-License-Identifier: Apache-2.0
"""The type of a finding, shared by every `check` command."""

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


def sort_diagnostics(diagnostics: Iterable[Diagnostic]) -> tuple[Diagnostic, ...]:
    """Put diagnostics in the one order every renderer prints them.

    Args:
        diagnostics: The findings, in any order.

    Returns:
        The findings sorted by `where`, then error, warning and note, then
        `message`, as plain strings (so `x[10]` sorts before `x[2]`).

    Raises:
        NotImplementedError: Until the implementation stage.
    """
    raise NotImplementedError
