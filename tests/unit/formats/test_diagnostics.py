# SPDX-License-Identifier: Apache-2.0
"""Tests of the renderer of diagnostics."""

import json

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


def test_keep_order_prints_the_diagnostics_as_given() -> None:
    """A caller that sorts by a rule of its own keeps its order in both renderers."""
    # Given a place on line 4 given before one on line 12, which plain strings
    # would sort the other way round
    given = [
        Diagnostic("error", "t.md:4", "first"),
        Diagnostic("error", "t.md:12", "second"),
    ]

    # When both renderers run with `keep_order`
    text = render_text(given, keep_order=True)
    data = json.loads(render_json(given, keep_order=True))

    # Then the text and the JSON are in the order given
    assert text == "error: t.md:4: first\nerror: t.md:12: second"
    assert [item["message"] for item in data] == ["first", "second"]


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_check_with_nothing_to_report_prints_the_sentence_it_is_given() -> None:
    """AC-8: text and JSON for no diagnostic."""
    # Given no diagnostic
    # When `render_check` runs with `passes="The contracts pass."`, in text and as JSON
    # Then the renderings are `The contracts pass.` and `[]`, each ending in a newline
