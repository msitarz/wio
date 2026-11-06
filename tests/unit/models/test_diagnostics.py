# SPDX-License-Identifier: Apache-2.0
"""Tests of `Diagnostic` and `sort_diagnostics`."""

import pytest

STUB = pytest.mark.skip(reason="a stub until the implementation stage")


@STUB
def test_diagnostics_sort_by_place_then_severity_then_message() -> None:
    """The one order of every renderer (AC-3)."""
    # Given a note at `b`, an error at `b`, an error at `a` and a warning at `a`.

    # When they are sorted with `sort_diagnostics`.

    # Then the order is the error at `a`, the warning at `a`, the error at `b`, the
    # note at `b`, and `x[10]` sorts before `x[2]`.


@STUB
def test_a_diagnostic_is_immutable() -> None:
    """A `Diagnostic` cannot change (AC-3)."""
    # Given a `Diagnostic`.

    # When a field is assigned.

    # Then it raises.
