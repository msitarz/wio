# SPDX-License-Identifier: Apache-2.0
"""What `wio templates directives` prints: the table of the directive grammar."""

from dataclasses import asdict
from typing import TYPE_CHECKING

lazy from wio.formats import encode_json

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.models.directives import DirectiveSpec


def render_reference(
    directives: Sequence[DirectiveSpec],
    combining: Sequence[DirectiveSpec],
    *,
    as_json: bool,
) -> str:
    """Render the table of directives and how they combine."""
    sections = (("directives", directives), ("combining", combining))
    return _as_json(sections) if as_json else _as_text(sections)


def _as_json(sections: Sequence[tuple[str, Sequence[DirectiveSpec]]]) -> str:
    """Render the sections as one compact JSON object."""
    found = {key: [asdict(spec) for spec in specs] for key, specs in sections}
    return encode_json(found) + "\n"


def _as_text(sections: Sequence[tuple[str, Sequence[DirectiveSpec]]]) -> str:
    """Render the sections as indented blocks under their headers."""
    return "\n".join(_section(header, specs) for header, specs in sections if specs)


def _section(header: str, specs: Sequence[DirectiveSpec]) -> str:
    """Render a section of blocks under a header."""
    return f"{header}:\n\n" + "\n".join(_block(spec) for spec in specs)


def _block(spec: DirectiveSpec) -> str:
    """Render one entry as a block of lines."""
    lines = [spec.name, f"  Syntax: {spec.syntax}"]
    lines.extend(f"  {line}" if line else "" for line in spec.meaning.splitlines())
    lines.extend(f"  Example: {example}" for example in spec.examples)
    return "\n".join(lines) + "\n"
