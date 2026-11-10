# SPDX-License-Identifier: Apache-2.0
"""Tests of the hooks that run `wio templates check` and the recipe that shows them."""

import pytest

SKIP = "Pending the implementation stage."


@pytest.mark.skip(reason=SKIP)
@pytest.mark.slow
def test_the_hook_returns_the_errors_of_an_edit_of_a_template() -> None:
    """AC-1: the command of the hook exits 2 with the diagnostics on stderr."""
    # Given the hook's command, a check that fails, and the `PostToolUse` input
    # for an edit of `.agents/wio/templates/feature.leaf.md`
    # When the command runs with that input, and again for an edit of
    # `.agents/wio/templates/sub/other.md`
    # Then each exits 2 with the diagnostics on standard error and nothing on
    # standard output


@pytest.mark.skip(reason=SKIP)
@pytest.mark.slow
def test_the_hook_is_silent_for_other_edits_and_for_a_check_that_passes() -> None:
    """AC-2: not a template, a passing check and a warning alone print nothing."""
    # Given the hook's command and a check that fails
    # When the command receives the input for an edit of `src/wio/cli/x.py`, of
    # `.agents/wio/config.toml` and of `.agents/wio/templates/notes.txt`; and
    # then, for an edit of a template, a check that passes and one whose only
    # finding is a warning
    # Then each exits 0 with no output


@pytest.mark.skip(reason=SKIP)
@pytest.mark.slow
def test_the_hook_does_not_block_an_edit_when_the_check_cannot_run() -> None:
    """AC-3: a check that exits with anything but 1 gives exit 0 and no output."""
    # Given the hook's command and a check that exits 2
    # When the command receives the input for an edit of a template
    # Then it exits 0 with no output


@pytest.mark.skip(reason=SKIP)
def test_prek_runs_the_check_when_a_template_is_in_the_commit() -> None:
    """AC-4: the hook matches the templates and passes them no file names."""
    # Given `prek.toml` and a staged template, and then a staged change to
    # `src/wio/cli/x.py` alone
    # When its `wio-templates` hook is read, with its `files` pattern applied to
    # each path
    # Then it runs `uv run wio templates check`, matches a template in any
    # subdirectory of the templates directory, does not match the other paths and
    # passes no file names


@pytest.mark.skip(reason=SKIP)
def test_the_workflow_describes_both_hooks() -> None:
    """AC-5: section 7 shows an entry and a `prek` hook for each check."""
    # Given `docs/workflow.md`
    # When its section 7 is read
    # Then it says that the config and the templates are checked after every
    # edit and before every commit that changes them, shows the
    # `.claude/settings.json` entry for each, names the `prek` hook of each, and
    # says that each project decides how its harness runs the checks
