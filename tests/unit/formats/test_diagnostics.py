# SPDX-License-Identifier: Apache-2.0
"""Tests of the renderer of diagnostics."""

import json
import subprocess
import sys

import pytest

from wio.formats import render_json, render_text
from wio.models.diagnostics import Diagnostic

LIST = [
    Diagnostic("error", "stages.x", "unknown stage"),
    Diagnostic("note", "a", "reserved"),
]


def test_text_and_json_follow_the_order_of_the_diagnostics() -> None:
    """Both renderers print the sorted list (AC-4)."""
    # Given an error at `stages.x` and a note at `a`

    # When both renderers run on it
    text = render_text(LIST)
    data = json.loads(render_json(LIST))

    # Then the text is the two lines in order and the JSON is an array of two
    # objects with `severity`, `where` and `message`, in the same order
    assert text == "note: a: reserved\nerror: stages.x: unknown stage"
    assert data == [
        {"severity": "note", "where": "a", "message": "reserved"},
        {"severity": "error", "where": "stages.x", "message": "unknown stage"},
    ]


def test_no_diagnostics_render_empty() -> None:
    """An empty list renders as nothing (AC-4)."""
    # Given an empty list
    empty: list[Diagnostic] = []

    # When both renderers run on it
    text = render_text(empty)
    rendered = render_json(empty)

    # Then the text is empty and the JSON is `[]`
    assert text == ""
    assert rendered == "[]"


@pytest.mark.slow
def test_rendering_text_does_not_import_json() -> None:
    """Importing the renderer stays light (AC-4)."""
    # Given a program that renders text in a new Python process
    program = (
        "import sys\n"
        "from wio.formats import render_text\n"
        "from wio.models.diagnostics import Diagnostic\n"
        "render_text([Diagnostic('note', 'a', 'm')])\n"
        "sys.stdout.write(str('json' in sys.modules))\n"
    )

    # When it runs
    done = subprocess.run(
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        check=True,
    )

    # Then `json` is not in `sys.modules`
    assert done.stdout == "False"
