# SPDX-License-Identifier: Apache-2.0
"""Tests of what `wio config check` prints and exits with."""

import pytest


def test_no_diagnostic_prints_nothing_in_text_and_an_empty_array_in_json() -> None:
    """AC-1: a valid config is silent as text and `[]` as JSON, both exit 0."""
    # Given a load without diagnostics
    # When it is reported as text and as JSON
    # Then the text is empty, the JSON is `[]\n` and both exit codes are 0
    pytest.skip("stub: the implementation stage writes this test")


def test_an_error_exits_1_and_a_warning_or_note_exits_0() -> None:
    """AC-1: only an error fails the check."""
    # Given loads with an error, with only a warning and with only a note
    # When each is reported
    # Then the exit codes are 1, 0 and 0, and every diagnostic is printed
    pytest.skip("stub: the implementation stage writes this test")


def test_each_text_diagnostic_is_a_line_in_the_order_given() -> None:
    """AC-1: `<severity>: <where>: <message>`, each ending in a newline."""
    # Given a load whose diagnostics are sorted, of every severity
    # When it is reported as text
    # Then there is one line per diagnostic, in the same order
    pytest.skip("stub: the implementation stage writes this test")
