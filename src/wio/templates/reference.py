# SPDX-License-Identifier: Apache-2.0
"""What `wio templates directives` prints: the table of the directive grammar."""

from dataclasses import asdict
from typing import TYPE_CHECKING
lazy import json

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.models.directives import DirectiveSpec


def render_reference(directives: Sequence[DirectiveSpec], *, as_json: bool) -> str:
    """Render the table of directives for a person or for a program.

    It prints the table's fields as they are and adds no text of its own, in the
    order of the table, without sorting or filtering. It reads nothing of the
    project, and it imports `json` only for the JSON form.

    Args:
        directives: The entries of the table, in its fixed order.
        as_json: Whether to render one JSON array instead of the indented list.

    Returns:
        The text for standard output. The human form has one block for each
        entry. A block has the name on a line and, indented by two spaces, a
        `Syntax:` line, the meaning with each of its lines indented by two
        spaces, an empty line of it left empty without trailing spaces, and an
        `Example:` line for each example, `Example: ` followed by the example
        heading as the table has it. One empty line separates blocks and none
        follows the last, so the text ends in exactly one line ending, and it is
        empty for an empty table. The JSON form is one compact array, as
        `list --json` writes it, ending in a line ending, with an object for
        each entry holding `name`, `syntax`, `meaning` and `examples` in that
        order, the last an array that is empty for an entry with no example, and
        `[]` for an empty table. The same table always gives the same text.
    """
    if as_json:
        return json.dumps([asdict(spec) for spec in directives]) + "\n"
    return "\n".join(_block(spec) for spec in directives)


def _block(spec: DirectiveSpec) -> str:
    """Render one entry as a block of lines.

    Args:
        spec: The entry of the table.

    Returns:
        The name, its syntax, its meaning and its examples, each line ending in a
        line ending.
    """
    lines = [spec.name, f"  Syntax: {spec.syntax}"]
    lines.extend(f"  {line}" if line else "" for line in spec.meaning.splitlines())
    lines.extend(f"  Example: {example}" for example in spec.examples)
    return "\n".join(lines) + "\n"
