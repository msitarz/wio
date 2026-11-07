# SPDX-License-Identifier: Apache-2.0
"""Tests of `Diagnostic` and `sort_diagnostics`."""

from dataclasses import FrozenInstanceError

import pytest

from wio.models.diagnostics import Diagnostic, sort_diagnostics


def test_diagnostics_sort_by_place_then_severity_then_message() -> None:
    """The one order of every renderer (AC-3)."""
    # Given a note at `b`, an error at `b`, an error at `a` and a warning at `a`
    note_b = Diagnostic("note", "b", "n")
    error_b = Diagnostic("error", "b", "e")
    error_a = Diagnostic("error", "a", "e")
    warning_a = Diagnostic("warning", "a", "w")
    wide = Diagnostic("error", "x[10]", "m")
    narrow = Diagnostic("error", "x[2]", "m")

    # When they are sorted with `sort_diagnostics`
    ordered = sort_diagnostics([note_b, error_b, error_a, warning_a])
    indexes = sort_diagnostics([narrow, wide])

    # Then the order is the error at `a`, the warning at `a`, the error at `b`,
    # the note at `b`, and `x[10]` sorts before `x[2]`
    assert ordered == (error_a, warning_a, error_b, note_b)
    assert indexes == (wide, narrow)


def test_a_diagnostic_is_immutable() -> None:
    """A `Diagnostic` cannot change (AC-3)."""
    # Given a Diagnostic and the name of one of its fields
    diagnostic = Diagnostic("error", "a", "m")
    name = "where"

    # When a field is assigned
    # Then it raises
    with pytest.raises(FrozenInstanceError):
        setattr(diagnostic, name, "b")
