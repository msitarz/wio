# SPDX-License-Identifier: Apache-2.0
"""Tests of the renderer of diagnostics."""

import json

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
