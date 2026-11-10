# SPDX-License-Identifier: Apache-2.0
"""What `wio templates directives` prints: the table of the directive grammar."""

from typing import TYPE_CHECKING

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
        entry, with the name on a line and under it, indented by two spaces, a
        `Syntax:` line, the meaning, each of its lines indented by two spaces,
        and an `Example:` line for each example, with one empty line between
        blocks and none after the last. The JSON form is one array, with an object
        for each entry holding `name`, `syntax`, `meaning` and `examples`, the
        last an array. The same table always gives the same text.
    """
    raise NotImplementedError
