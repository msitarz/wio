# SPDX-License-Identifier: Apache-2.0
"""Tests for the hook that checks the config after an agent edits it."""

import pytest


def test_an_edit_of_the_config_with_an_error_exits_2() -> None:
    """AC-3: the diagnostics go to standard error for the model."""
    # Given the hook's JSON for an edit of the config, and a check that exits 1
    # When the script reads it on standard input
    # Then it prints the diagnostics to standard error and returns 2
    pytest.skip("stub: the implementation stage writes this test")


@pytest.mark.parametrize("case", ["python file", "clean config", "not JSON"])
def test_other_edits_and_a_clean_config_exit_0_silently(case: str) -> None:
    """AC-3: an edit of another file, a config without errors, bad JSON."""
    # Given the hook's JSON for `case`
    # When the script reads it
    # Then it returns 0 and writes nothing, and runs no check for the first and last
    del case
    pytest.skip("stub: the implementation stage writes this test")


def test_a_check_that_cannot_run_is_not_the_agents_to_fix() -> None:
    """AC-3: a check that exits 2 leaves the hook at 0."""
    # Given the hook's JSON for an edit of the config, and a check that exits 2
    # When the script reads it
    # Then it returns 0 and writes nothing
    pytest.skip("stub: the implementation stage writes this test")
