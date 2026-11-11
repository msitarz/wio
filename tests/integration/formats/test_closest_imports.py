# SPDX-License-Identifier: Apache-2.0
"""Tests of the closest key that need a fresh interpreter."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.slow
def test_difflib_and_json_load_only_when_they_are_needed() -> None:
    """AC-3: no import at start, nor in a run that finds no mistyped key."""
    # Given a new process, a valid config and valid templates
    # When `wio.formats` is imported, the config and templates checks run in text form,
    # `sys.modules` is read, then `closest_key` is called and it is read again
    # Then neither `difflib` nor `json` is there the first time, and `difflib` is there
    # the second
