# SPDX-License-Identifier: Apache-2.0
"""What `wio config check` prints and exits with, from one load.

The module renders through `wio.formats` and imports `json` only for `--json`,
as the rules of the command line ask.
"""

from typing import TYPE_CHECKING

lazy from wio.formats import render_json, render_text

if TYPE_CHECKING:
    from wio.config.loader import Loaded


def report(loaded: Loaded, *, as_json: bool) -> tuple[str, int]:
    """Say what `wio config check` writes and how it exits for one load.

    The diagnostics of `loaded` are already sorted, so none is reordered here.

    Args:
        loaded: What `load_config` returned: every diagnostic of the shape and of
            `wio.config.CHECKS`, with a syntax error as the one diagnostic.
        as_json: Whether to write an array of objects with `severity`, `where`
            and `message`, `[]` for none, instead of one line per diagnostic.

    Returns:
        The text for standard output, each diagnostic ending in a newline, empty
        for none in text, and the exit code: 0 when no diagnostic is an error, so
        warnings and notes never fail a check, and 1 when any is.
    """
    found = loaded.diagnostics
    code = int(any(item.severity == "error" for item in found))
    if as_json:
        return f"{render_json(found)}\n", code
    text = render_text(found)
    return (f"{text}\n" if text else ""), code
