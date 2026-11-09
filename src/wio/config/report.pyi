# SPDX-License-Identifier: Apache-2.0
"""What `wio config check` prints and exits with, from one load.

The stub is the spec until the implementation stage replaces it with a `.py` of
the same annotations. The module renders through `wio.formats` and imports
`json` only for `--json`, as the rules of the command line ask.
"""

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
    ...
