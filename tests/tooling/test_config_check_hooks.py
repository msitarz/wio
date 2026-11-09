# SPDX-License-Identifier: Apache-2.0
"""Tests of the hooks that run `wio config check` and the recipe that shows them."""

import pytest


def test_prek_runs_the_check_when_only_the_config_changes() -> None:
    """AC-2: the hook matches the config and passes it no file names."""
    # Given `prek.toml`
    # When its hook for the config is read
    # Then it runs `wio config check`, matches only the config, no filenames
    pytest.skip("stub: the implementation stage writes this test")


def test_claude_settings_run_the_check_beside_the_formatter() -> None:
    """AC-3: one `PostToolUse` hook runs `uv run wio config check`."""
    # Given `.claude/settings.json`
    # When its `PostToolUse` hooks are read
    # Then one runs after `Edit`, `Write` and `MultiEdit` and its command runs
    # `uv run wio config check`, and the formatter stays
    pytest.skip("stub: the implementation stage writes this test")


@pytest.mark.slow
def test_the_hook_returns_the_errors_of_an_edit_of_the_config() -> None:
    """AC-3: the command of the hook exits 2 with the diagnostics on stderr."""
    # Given the hook's JSON for an edit of the config, and a config with an error
    # When the command of the hook runs with that JSON on standard input
    # Then it prints the diagnostics to standard error and exits 2
    pytest.skip("stub: the implementation stage writes this test")


@pytest.mark.slow
@pytest.mark.parametrize("case", ["another TOML file", "config without errors"])
def test_the_hook_is_silent_for_other_edits_and_a_clean_config(case: str) -> None:
    """AC-3: the command of the hook exits 0 and prints nothing."""
    # Given the hook's JSON for `case`
    # When the command of the hook runs with it on standard input
    # Then it exits 0 and prints nothing
    del case
    pytest.skip("stub: the implementation stage writes this test")


def test_the_workflow_shows_the_recipe() -> None:
    """AC-4: the doc has the entry, "each project" and the prek hook."""
    # Given `docs/workflow.md`
    # When it is read
    # Then it shows the `PostToolUse` entry, says each project chooses its own
    # and writes `wio config check` for a global install, and says when the prek
    # hook runs
    pytest.skip("stub: the implementation stage writes this test")
