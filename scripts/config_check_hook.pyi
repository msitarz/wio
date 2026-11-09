# SPDX-License-Identifier: Apache-2.0
"""The Claude Code hook that checks the config after an agent edits it.

The stub is the spec until the implementation stage replaces it with a `.py`.
Claude Code runs the script as a `PostToolUse` hook after `Edit`, `Write` and
`MultiEdit` and passes it the tool call as JSON on standard input. It uses the
standard library alone, so it starts without importing `wio`, and it runs wio
through `uv run wio`, so no `wio` need be on `PATH`. It is the recipe that
`docs/workflow.md` shows, and it exits 2, which Claude Code reads as "feed
standard error to the model", only when the check found an error.
"""

from collections.abc import Callable
from subprocess import CompletedProcess
from typing import TextIO

CONFIG_PATH: str
"""The config file relative to the repository root: `.agents/wio/config.toml`.

It repeats `wio.config.loader.CONFIG_PATH` on purpose, because the script uses
the standard library alone and `scripts` may not import `wio`.
"""

def is_config_edit(document: object) -> bool:
    """Say whether a hook document is an edit of the config file.

    Args:
        document: The decoded JSON on standard input, of any shape.

    Returns:
        True when `document` is an object whose `tool_input.file_path` is a
        string that names the config file, as an absolute path under the
        repository or relative to it. False for every other document, including
        one without those keys.
    """
    ...

def run_check() -> CompletedProcess[str]:
    """Run `uv run wio config check` and capture its streams.

    Returns:
        The finished process, with the output as text. It is the default
        runner of `main`, and a test passes another.
    """
    ...

def main(
    stdin: TextIO,
    stderr: TextIO,
    run: Callable[[], CompletedProcess[str]] = run_check,
) -> int:
    """Check the config when the edit that stdin describes was of the config.

    Args:
        stdin: The hook's JSON document. A document that is not JSON is ignored.
        stderr: Where the diagnostics go, which Claude Code gives the model.
        run: Runs the check; called only for an edit of the config.

    Returns:
        2 when the check exits 1, after writing its diagnostics to `stderr`; 0
        for every other document, for a check without errors, and for a check
        that could not run, which is the user's to see and not the agent's to
        fix. Nothing is written for a 0.
    """
    ...
