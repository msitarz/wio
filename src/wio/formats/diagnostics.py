# SPDX-License-Identifier: Apache-2.0
"""The renderer of diagnostics, as text or JSON."""

from dataclasses import asdict
from typing import TYPE_CHECKING
lazy import json

from wio.models.diagnostics import sort_diagnostics

if TYPE_CHECKING:
    from collections.abc import Iterable

    from wio.models.diagnostics import Diagnostic


def encode_json(
    value: object, *, indent: int | None = None, ensure_ascii: bool = True
) -> str:
    """Encode a value as JSON, loading the encoder on first use.

    Args:
        value: The JSON-serializable value.
        indent: The indentation width, or none for a single line.
        ensure_ascii: Escape non-ASCII characters when true.

    Returns:
        JSON text without a trailing newline.
    """
    return json.dumps(value, indent=indent, ensure_ascii=ensure_ascii)


def render_text(diagnostics: Iterable[Diagnostic]) -> str:
    """Render diagnostics as one line each in `sort_diagnostics` order.

    Returns:
        One `error|warning|note: <where>: <message>` line per finding, joined
        by newlines; empty for none.
    """
    ordered = sort_diagnostics(diagnostics)
    return "\n".join(f"{d.severity}: {d.where}: {d.message}" for d in ordered)


def render_json(diagnostics: Iterable[Diagnostic]) -> str:
    """Render diagnostics as a JSON array in `sort_diagnostics` order.

    `json` is imported only when this is called, so a process that renders
    text never loads it.

    Returns:
        A JSON array of objects with `severity`, `where` and `message`; `[]`
        for none.
    """
    ordered = sort_diagnostics(diagnostics)
    return encode_json([asdict(d) for d in ordered])


def render_check(
    diagnostics: Iterable[Diagnostic], *, as_json: bool, passes: str
) -> str:
    """Render the result of a `check` command.

    `json` is imported only when `as_json` is set.
    """
    ordered = sort_diagnostics(diagnostics)
    if as_json:
        return render_json(ordered) + "\n"
    if not ordered:
        return passes + "\n"
    return render_text(ordered) + "\n"
