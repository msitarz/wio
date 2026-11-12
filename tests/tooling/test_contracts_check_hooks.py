# SPDX-License-Identifier: Apache-2.0
"""Test stubs of the hooks that run `wio contracts check`.

Each stub is a scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


def test_the_hook_returns_the_errors_of_an_edit_of_a_contract() -> None:
    """AC-1: the command of the hook exits 2 with the diagnostics on stderr."""
    # Given the hook's command and a fake `uv` that prints a diagnostic and exits 1
    # When the command receives the input for an edit of a contract, in the Works
    # directory and in a subdirectory of a Work
    # Then each exits 2 with that diagnostic on standard error and nothing on
    # standard output, and the fake `uv` was called with `run wio contracts check`
    raise NotImplementedError


def test_the_hook_is_silent_when_the_edit_is_not_a_contract() -> None:
    """AC-2: a file that is not a contract prints nothing and calls no check."""
    # Given the hook's command and a fake `uv` for a check that fails
    # When the command receives the input for an edit of a source file, the config,
    # a template and a file of the Works directory that is not Markdown
    # Then each exits 0 with no output, and the check was not called
    raise NotImplementedError


def test_the_hook_is_silent_for_a_check_that_passes() -> None:
    """AC-2: a passing check, and one that only warns, print nothing."""
    # Given the hook's command and a fake `uv` for a check that exits 0 with the
    # message of a pass, and with a warning
    # When the command receives the input for an edit of a contract
    # Then it ran the check and exits 0 with no output
    raise NotImplementedError


def test_the_hook_does_not_block_an_edit_when_the_check_cannot_run() -> None:
    """AC-3: a check that exits with anything but 1 gives exit 0 and no output."""
    # Given the hook's command and a fake `uv` for a check that exits 2, and one
    # that exits 127
    # When the command receives the input for an edit of a contract
    # Then it ran the check and exits 0 with no output
    raise NotImplementedError


def test_prek_runs_the_check_when_a_contract_is_in_the_commit() -> None:
    """AC-4: the hook matches the Works directory and passes no file names."""
    # Given `prek.toml`
    # When its hook for the contracts is read
    # Then it runs `uv run wio contracts check`, matches a `.md` file in any
    # subdirectory of the Works directory and no other path, and passes no file
    # names
    raise NotImplementedError


def test_a_commit_that_changes_a_contract_with_an_error_is_refused() -> None:
    """AC-4: `prek` fails the hook and prints the diagnostic of the check."""
    # Given a git repository with this repository's `prek.toml`, a minimal config,
    # and a staged contract whose `depends_on` names an id that no Work has
    # When `prek` runs the hook on the staged files
    # Then the hook fails and prints the diagnostic that names the unknown
    # dependency
    raise NotImplementedError


def test_a_commit_with_no_contract_does_not_run_the_hook() -> None:
    """AC-4: the hook is skipped when no contract is staged."""
    # Given a git repository in which only a source file is staged
    # When `prek` runs the hook on the staged files
    # Then its output marks the hook `(no files to check)Skipped`
    raise NotImplementedError
