# SPDX-License-Identifier: Apache-2.0
"""Helpers that the unit tests of the discovery of Works share."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from wio.models.diagnostics import Diagnostic


def where(diagnostics: Iterable[Diagnostic]) -> list[str]:
    """List the places of some diagnostics.

    Args:
        diagnostics: The diagnostics.

    Returns:
        Their places, in their order.
    """
    return [d.where for d in diagnostics]


def paths(items: Iterable[Path]) -> list[str]:
    """List some paths written with `/`.

    Args:
        items: The paths.

    Returns:
        Their strings, in their order.
    """
    return [p.as_posix() for p in items]
