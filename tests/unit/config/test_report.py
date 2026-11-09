# SPDX-License-Identifier: Apache-2.0
"""Tests of what `wio config check` prints and exits with."""

import json

from wio.config.loader import Loaded
from wio.config.report import report
from wio.models.diagnostics import Diagnostic

ERROR = Diagnostic("error", "works.nonsense", "unknown key `nonsense`")
WARNING = Diagnostic("warning", "stages.a", "unused")
NOTE = Diagnostic("note", "stages.b", "see also")


def _load(*found: Diagnostic) -> Loaded:
    """Make a load that holds diagnostics and nothing else.

    Args:
        *found: The diagnostics, already sorted.

    Returns:
        The load.
    """
    return Loaded(None, found, frozendict())


def test_no_diagnostic_prints_nothing_in_text_and_an_empty_array_in_json() -> None:
    """AC-1: a valid config is silent as text and `[]` as JSON, both exit 0."""
    # Given a load without diagnostics
    loaded = _load()

    # When it is reported as text and as JSON
    text = report(loaded, as_json=False)
    as_json = report(loaded, as_json=True)

    # Then the text is empty, the JSON is `[]` and both exit codes are 0
    assert text == ("", 0)
    assert as_json == ("[]\n", 0)


def test_an_error_exits_1_and_a_warning_or_note_exits_0() -> None:
    """AC-1: only an error fails the check."""
    # Given loads with an error, with only a warning and with only a note
    with_error = _load(ERROR, WARNING)
    with_warning = _load(WARNING)
    with_note = _load(NOTE)

    # When each is reported
    codes = [
        report(loaded, as_json=False)[1]
        for loaded in (with_error, with_warning, with_note)
    ]

    # Then the exit codes are 1, 0 and 0, and every diagnostic is printed
    assert codes == [1, 0, 0]
    assert report(with_error, as_json=False)[0].count("\n") == 2


def test_each_text_diagnostic_is_a_line_in_the_order_given() -> None:
    """AC-1: `<severity>: <where>: <message>`, each ending in a newline."""
    # Given a load whose diagnostics are sorted, of every severity
    loaded = _load(WARNING, NOTE, Diagnostic("error", "z", "m"))

    # When it is reported as text
    text, _ = report(loaded, as_json=False)

    # Then there is one line per diagnostic, in the same order
    assert text == (
        "warning: stages.a: unused\nnote: stages.b: see also\nerror: z: m\n"
    )


def test_json_is_an_array_of_objects_in_the_order_given() -> None:
    """AC-1: each object has `severity`, `where` and `message`."""
    # Given a load with an error and a warning
    loaded = _load(WARNING, ERROR)

    # When it is reported as JSON
    text, code = report(loaded, as_json=True)

    # Then the array holds both objects in that order and the run fails
    assert json.loads(text) == [
        {"severity": "warning", "where": "stages.a", "message": "unused"},
        {
            "severity": "error",
            "where": "works.nonsense",
            "message": "unknown key `nonsense`",
        },
    ]
    assert code == 1
