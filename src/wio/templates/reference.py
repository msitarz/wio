# SPDX-License-Identifier: Apache-2.0
"""What `wio templates directives` prints: the table of the directive grammar."""

from dataclasses import asdict
from typing import TYPE_CHECKING
lazy import json

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.models.directives import DirectiveSpec


def render_reference(
    directives: Sequence[DirectiveSpec],
    combining: Sequence[DirectiveSpec],
    *,
    as_json: bool,
) -> str:
    """Render the table of directives and how they combine.

    It prints the fields of the entries as they are and adds no text of its own
    but the two section headers, in the order given, without sorting or
    filtering. It reads nothing of the project, and it imports `json` only for
    the JSON form.

    Args:
        directives: The entries of the table, in its fixed order.
        combining: The entries that say how directives combine in one comment,
            of the same shape as those of the table.
        as_json: Whether to render one JSON object instead of the indented list.

    Returns:
        The text for standard output. The human form has a section `directives:`
        and then a section `combining:`, each a header line, an empty line and
        one block for each entry. A block has the name on a line and, indented by
        two spaces, a `Syntax:` line, the meaning with each of its lines indented
        by two spaces, an empty line of it left empty without trailing spaces,
        and an `Example:` line for each example, `Example: ` followed by the
        example heading as the table has it. One empty line separates blocks and
        sections and none follows the last, so the text ends in exactly one line
        ending. A section with no entry is left out, so the text is empty when
        both are empty. The JSON form is one compact object, as `list --json`
        writes its array, ending in a line ending, with the keys `directives`
        and `combining` in that order, each an array of objects holding `name`,
        `syntax`, `meaning` and `examples` in that order, the last an array that
        is empty for an entry with no example; both keys are present even when
        their arrays are empty. The same entries always give the same text.
    """
    sections = (("directives", directives), ("combining", combining))
    return _as_json(sections) if as_json else _as_text(sections)


def _as_json(sections: Sequence[tuple[str, Sequence[DirectiveSpec]]]) -> str:
    """Render the sections as one compact JSON object.

    Args:
        sections: The key and the entries of each section, in order.

    Returns:
        The object, with an array for each key, ending in a line ending.
    """
    found = {key: [asdict(spec) for spec in specs] for key, specs in sections}
    return json.dumps(found) + "\n"


def _as_text(sections: Sequence[tuple[str, Sequence[DirectiveSpec]]]) -> str:
    """Render the sections as indented blocks under their headers.

    Args:
        sections: The header and the entries of each section, in order.

    Returns:
        The sections that have an entry, with an empty line between them.
    """
    return "\n".join(_section(header, specs) for header, specs in sections if specs)


def _section(header: str, specs: Sequence[DirectiveSpec]) -> str:
    """Render a section of blocks under a header.

    Args:
        header: The section's name, written with a colon.
        specs: The entries of the section.

    Returns:
        The header line, an empty line and the blocks, each ending in a line
        ending, with an empty line between blocks.
    """
    return f"{header}:\n\n" + "\n".join(_block(spec) for spec in specs)


def _block(spec: DirectiveSpec) -> str:
    """Render one entry as a block of lines.

    Args:
        spec: The entry.

    Returns:
        The name, its syntax, its meaning and its examples, each line ending in a
        line ending.
    """
    lines = [spec.name, f"  Syntax: {spec.syntax}"]
    lines.extend(f"  {line}" if line else "" for line in spec.meaning.splitlines())
    lines.extend(f"  Example: {example}" for example in spec.examples)
    return "\n".join(lines) + "\n"
