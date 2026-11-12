# SPDX-License-Identifier: Apache-2.0
"""Helpers that the unit tests of the discovery of Works share."""

from pathlib import Path
from typing import TYPE_CHECKING

from wio.models.frozen import freeze
from wio.models.works import Work

if TYPE_CHECKING:
    from collections.abc import Iterable

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


def work_with_id(work_id: str) -> Work:
    """Build a Work that has an id and sits at `<id>/README.md`.

    Args:
        work_id: The id.

    Returns:
        The Work, with nothing else set.
    """
    return Work(
        id=work_id,
        title=None,
        path=Path(work_id) / "README.md",
        template=None,
        roots=(),
        depends_on=(),
        actions=freeze({}),
    )
