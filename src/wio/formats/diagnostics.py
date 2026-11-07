# SPDX-License-Identifier: Apache-2.0
"""The renderer of diagnostics, as text or JSON."""

from dataclasses import asdict
from typing import TYPE_CHECKING

from wio.models.diagnostics import sort_diagnostics

if TYPE_CHECKING:
    from collections.abc import Iterable

    from wio.models.diagnostics import Diagnostic


def render_text(diagnostics: Iterable[Diagnostic]) -> str:
    """Render diagnostics as one line each.

    Args:
        diagnostics: The findings, in any order.

    Returns:
        One `error|warning|note: <where>: <message>` line per finding in the
        order of `sort_diagnostics`, joined by newlines; empty for none.

    """
    ordered = sort_diagnostics(diagnostics)
    return "\n".join(f"{d.severity}: {d.where}: {d.message}" for d in ordered)


def render_json(diagnostics: Iterable[Diagnostic]) -> str:
    """Render diagnostics as a JSON array.

    `json` is imported only when this is called, so a process that renders
    text never loads it.

    Args:
        diagnostics: The findings, in any order.

    Returns:
        A JSON array of objects with `severity`, `where` and `message`, in the
        order of `sort_diagnostics`; `[]` for none.

    """
    import json

    ordered = sort_diagnostics(diagnostics)
    return json.dumps([asdict(d) for d in ordered])
