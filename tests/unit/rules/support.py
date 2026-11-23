# SPDX-License-Identifier: Apache-2.0
"""Helpers that the tests of the rule readers share."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from wio.models.diagnostics import Diagnostic


def kinds(diagnostics: Iterable[Diagnostic]) -> list[tuple[str, str]]:
    """List the severity and the place of each diagnostic.

    Args:
        diagnostics: What a reader or the discovery reported.

    Returns:
        A pair for each diagnostic, in the order given.
    """
    return [(d.severity, d.where) for d in diagnostics]
