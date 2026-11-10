# SPDX-License-Identifier: Apache-2.0
"""What `wio templates list` prints."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from wio.models.template import Template


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
    raise NotImplementedError
