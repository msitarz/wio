# SPDX-License-Identifier: Apache-2.0
"""Render the selected rows in the two forms of the log command.

Rendering uses the report alone, so it treats live and retired Works alike.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.log.show import Report


def render(report: Report, *, as_json: bool) -> str:
    """Render one report in the selected output form.

    The JSON document preserves field order and full commit ids. Text displays
    abbreviated commits and leaves the skip count to a separate diagnostic.

    Args:
        report: Selected rows and the global skip count.
        as_json: Whether to produce a JSON document in place of text.

    Returns:
        A JSON document with a final newline even when no Works are selected.
        The text form has a final newline when it has any rows, and is empty
        otherwise.
    """
    raise NotImplementedError
