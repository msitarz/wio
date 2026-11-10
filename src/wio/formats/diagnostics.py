# SPDX-License-Identifier: Apache-2.0
"""The renderer of diagnostics, as text or JSON."""

from dataclasses import asdict
from typing import TYPE_CHECKING

from wio.models.diagnostics import sort_diagnostics

if TYPE_CHECKING:
    from collections.abc import Iterable

    from wio.models.diagnostics import Diagnostic


def render_text(diagnostics: Iterable[Diagnostic], *, keep_order: bool = False) -> str:
    """Render diagnostics as one line each.

    Args:
        diagnostics: The findings, in any order.
        keep_order: Print them in the order given, for a caller that sorts by a
            rule of its own, instead of the order of `sort_diagnostics`.

    Returns:
        One `error|warning|note: <where>: <message>` line per finding in the
        order of `sort_diagnostics`, or as given with `keep_order`, joined by
        newlines; empty for none.

    """
    ordered = tuple(diagnostics) if keep_order else sort_diagnostics(diagnostics)
    return "\n".join(f"{d.severity}: {d.where}: {d.message}" for d in ordered)


def render_json(diagnostics: Iterable[Diagnostic], *, keep_order: bool = False) -> str:
    """Render diagnostics as a JSON array.

    `json` is imported only when this is called, so a process that renders
    text never loads it.

    Args:
        diagnostics: The findings, in any order.
        keep_order: Print them in the order given, for a caller that sorts by a
            rule of its own, instead of the order of `sort_diagnostics`.

    Returns:
        A JSON array of objects with `severity`, `where` and `message`, in the
        order of `sort_diagnostics`, or as given with `keep_order`; `[]` for none.

    """
    import json

    ordered = tuple(diagnostics) if keep_order else sort_diagnostics(diagnostics)
    return json.dumps([asdict(d) for d in ordered])
