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


def render_check(
    diagnostics: Iterable[Diagnostic], *, as_json: bool, passes: str
) -> str:
    """Render the result of a `check` command, in the order given.

    `json` is imported only when `as_json` is set.

    Args:
        diagnostics: The findings, already in the order the command prints them.
        as_json: Whether to write the JSON array instead of the text.
        passes: The sentence that says nothing was found, such as `The
            templates pass.`.

    Returns:
        With `as_json`, the array of `severity`, `where` and `message` objects,
        `[]` for none, ending in a newline. Otherwise `passes` when there is no
        diagnostic, and the `<severity>: <where>: <message>` lines when there are
        some, each ending in a newline.
    """
    raise NotImplementedError
