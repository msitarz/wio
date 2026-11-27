# SPDX-License-Identifier: Apache-2.0
"""What `wio templates list` prints."""

import re
from itertools import groupby
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

lazy from wio.formats import encode_json

if TYPE_CHECKING:
    from collections.abc import Iterable

    from wio.models.template import Template

_ENTRY = "[entry]"
_OUTER_EMPTY = re.compile(r"\A(?:[ \t]*\r?\n)+|(?:\r?\n[ \t]*)+\Z")


def render_list(templates: Iterable[Template], *, as_json: bool) -> str:
    """Render templates for a person or for a program.

    Args:
        templates: The templates to show, in any order.
        as_json: Whether to render one JSON array instead of the grouped text.

    Returns:
        The text for standard output, ending in a newline, and empty for no
        template in the human form. The human form groups the templates by kind
        in sorted order with one empty line between kinds, each on a line with
        its name, an `[entry]` mark and its `shape:`, and its description under
        it, each line as written. The JSON form is one array sorted by kind and
        then name, each object with `name`, `kind`, `shape`, `entry`,
        `description` and `path`, relative to the repository root and with `/`,
        `null` for a missing shape or description, and `[]` for none. It imports
        `json` only for the JSON form.
    """
    ordered = sorted(templates, key=lambda template: (template.kind, template.name))
    if as_json:
        return encode_json([_as_object(template) for template in ordered]) + "\n"
    groups = (
        _group(kind, list(members))
        for kind, members in groupby(ordered, key=lambda template: template.kind)
    )
    return "\n".join(groups)


def _as_object(template: Template) -> dict[str, object]:
    """Describe a template as plain data for JSON."""
    return {
        "name": template.name,
        "kind": template.kind,
        "shape": template.shape,
        "entry": template.entry,
        "description": template.description,
        "path": PurePosixPath(template.path).as_posix(),
    }


def _group(kind: str, members: list[Template]) -> str:
    """Render the templates of one kind."""
    width = max(len(template.name) for template in members)
    marked = any(template.entry for template in members)
    lines = [kind]
    for template in members:
        lines.append(_line(template, width, marked=marked))
        lines.extend(_description(template.description))
    return "\n".join(lines) + "\n"


def _line(template: Template, width: int, *, marked: bool) -> str:
    """Render one template's line."""
    columns = [template.name.ljust(width)]
    if marked:
        columns.append(_ENTRY if template.entry else " " * len(_ENTRY))
    if template.shape is not None:
        columns.append(f"shape: {template.shape}")
    return "  " + " ".join(columns).rstrip()


def _description(description: str | None) -> list[str]:
    """Lay out a description under its template."""
    if description is None:
        return []
    text = _OUTER_EMPTY.sub("", description)
    lines = [line.rstrip() for line in text.splitlines()]
    return [f"    {line}" if line else "" for line in lines]
