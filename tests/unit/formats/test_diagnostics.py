# SPDX-License-Identifier: Apache-2.0
"""Tests of the renderer of diagnostics."""

import pytest

STUB = pytest.mark.skip(reason="a stub until the implementation stage")


@STUB
def test_text_and_json_follow_the_order_of_the_diagnostics() -> None:
    """Both renderers print the sorted list (AC-4)."""
    # Given an error at `stages.x` and a note at `a`.

    # When both renderers run on it.

    # Then the text is the two lines in order and the JSON is an array of two
    # objects with `severity`, `where` and `message`, in the same order.


@STUB
def test_no_diagnostics_render_empty() -> None:
    """An empty list renders as nothing (AC-4)."""
    # Given an empty list.

    # When both renderers run on it.

    # Then the text is empty and the JSON is `[]`.


@STUB
def test_rendering_text_does_not_import_json() -> None:
    """Importing the renderer stays light (AC-4)."""
    # Given a new Python process.

    # When it imports `wio.formats` and calls `render_text`.

    # Then `json` is not in `sys.modules`.
