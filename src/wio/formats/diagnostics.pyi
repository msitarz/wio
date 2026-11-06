# SPDX-License-Identifier: Apache-2.0
"""The renderer of diagnostics, as text or JSON.

The stub is the spec until the implementation stage replaces it with a `.py`
of the same annotations.
"""

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
    ...

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
    ...
