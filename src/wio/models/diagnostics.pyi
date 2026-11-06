# SPDX-License-Identifier: Apache-2.0
"""The type of a finding, shared by every `check` command.

The stub is the spec until the implementation stage replaces it with a `.py`
of the same annotations.
"""

from collections.abc import Iterable
from typing import Literal

type Severity = Literal["error", "warning", "note"]

class Diagnostic:
    """One finding of a check: how serious, where and what.

    It is immutable, and `where` is a plain string, such as a key path.
    """

    severity: Severity
    """How serious the finding is."""
    where: str
    """The place of the finding, compared as a plain string."""
    message: str
    """What is wrong or worth knowing."""

def sort_diagnostics(diagnostics: Iterable[Diagnostic]) -> tuple[Diagnostic, ...]:
    """Put diagnostics in the one order every renderer prints them.

    Args:
        diagnostics: The findings, in any order.

    Returns:
        The findings sorted by `where`, then error, warning and note, then
        `message`, as plain strings (so `x[10]` sorts before `x[2]`).
    """
    ...
