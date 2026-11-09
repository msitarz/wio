# SPDX-License-Identifier: Apache-2.0
"""Tests of the hooks that run `wio config check` and the recipe that shows them."""

import pytest


def test_prek_runs_the_check_when_only_the_config_changes() -> None:
    """AC-2: the hook matches the config and passes it no file names."""
    # Given `prek.toml`
    # When its hook for the config is read
    # Then it runs `wio config check`, matches only the config, no filenames
    pytest.skip("stub: the implementation stage writes this test")


def test_claude_settings_run_the_script_beside_the_formatter() -> None:
    """AC-3: one `PostToolUse` hook runs the script after the three edit tools."""
    # Given `.claude/settings.json`
    # When its `PostToolUse` hooks are read
    # Then one runs the script for `Edit`, `Write` and `MultiEdit`, the formatter stays
    pytest.skip("stub: the implementation stage writes this test")


def test_the_workflow_shows_the_recipe() -> None:
    """AC-4: the doc has the script, the entry, "each project" and the prek hook."""
    # Given `docs/workflow.md`
    # When it is read
    # Then it shows the script and the `PostToolUse` entry, says each project
    # chooses its own, and says when the prek hook runs
    pytest.skip("stub: the implementation stage writes this test")
