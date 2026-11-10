# SPDX-License-Identifier: Apache-2.0
"""Tests of `wio templates directives` that need a fresh interpreter."""

import ast
import subprocess
import sys

import pytest

_PROBE = """
import sys
from wio.cli import main
from wio.io.adapters import SystemStdio
code = main(["templates", "directives", *sys.argv[1:]], SystemStdio())
names = ("json", "tomllib", "tomlkit", "markdown_it")
sys.stderr.write(repr([code, [name in sys.modules for name in names]]))
"""


def _run(*arguments: str) -> tuple[int, list[bool]]:
    """Run the command in a new process and read which parsers it loaded.

    Args:
        *arguments: The arguments after `directives`.

    Returns:
        The exit code, and whether each of `json`, `tomllib`, `tomlkit` and
        `markdown_it` was in `sys.modules` at the end.
    """
    done = subprocess.run(
        [sys.executable, "-c", _PROBE, *arguments],
        capture_output=True,
        text=True,
        check=True,
    )
    code, loaded = ast.literal_eval(done.stderr)
    return code, loaded


@pytest.mark.slow
def test_the_listing_loads_no_parser_or_writer() -> None:
    """AC-4: without `--json` none of `json`, `tomllib`, `tomlkit`, `markdown_it`."""
    # Given a new Python process
    # When `main(["templates", "directives"], stdio)` runs in it and `sys.modules`
    # is read
    code, loaded = _run()

    # Then none of the four modules is there
    assert (code, loaded) == (0, [False, False, False, False])


@pytest.mark.slow
def test_the_json_form_loads_json_and_nothing_else_of_the_four() -> None:
    """AC-4: `--json` imports `json` and still no parser or writer."""
    # Given a new Python process
    # When `main(["templates", "directives", "--json"], stdio)` runs in it and
    # `sys.modules` is read
    code, loaded = _run("--json")

    # Then `json` is there and `tomllib`, `tomlkit` and `markdown_it` are not
    assert (code, loaded) == (0, [True, False, False, False])
