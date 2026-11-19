# SPDX-License-Identifier: Apache-2.0
"""Contract scenarios for the log show command.

The scenarios describe the CLI output and the behavior across event files.
"""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize("args", [[], ["-h"]])
def test_log_help_names_show(wio: Wio, args: list[str]) -> None:
    """AC-1 makes show discoverable without locating a repository.

    Args:
        wio: The command facade with no registered repository.
        args: Arguments following log.
    """
    # Given a working directory with no repository.

    # When help is requested.
    output = wio.run(["log", *args])

    # Then help names show and exits successfully.
    assert output.exit_code == 0
    assert "show" in output.stdout
    assert output.stderr == ""


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize("args", [["nonsense"], ["--json"], ["show", "a", "b"]])
def test_log_rejects_invalid_usage(wio: Wio, args: list[str]) -> None:
    """AC-1 rejects unknown forms and misplaced or extra arguments.

    Args:
        wio: The command facade with no registered repository.
        args: Invalid arguments following log.
    """
    # Given a working directory with no repository.

    # When the invalid command runs.
    output = wio.run(["log", *args])

    # Then there is a usage error on standard error only.
    assert output.exit_code == 2
    assert output.stdout == ""
    assert "error:" in output.stderr


@pytest.mark.channels(Channel.CLI)
def test_show_without_a_log_returns_an_empty_document(wio: Wio) -> None:
    """AC-4 wires show to the ports of a real clone.

    Args:
        wio: The facade that initializes the clone and runs the real command.
    """
    # Given a real repository with no log directory.
    wio.fixture("config/rich")

    # When show is called with the JSON option.
    output = wio.run(["log", "show", "--json"])

    # Then the resulting report is empty and the command succeeds.
    assert output.exit_code == 0
    assert output.stdout == '{"works": {}, "skipped": 0}\n'
    assert output.stderr == ""


def test_latest_context() -> None:
    """AC-2 selects context and positions rows by event time.

    The scenario exercises the report through the log command.
    """
    # Given architecture at 10:09, wiring at 10:07, then older architecture entries.
    # When log show or its parent command runs.
    # Then wiring precedes the latest architecture context, with its own session.
    pytest.skip("Pending log show implementation")


def test_session_labels() -> None:
    """AC-2 displays each session shape.

    The scenario exercises the report through the log command.
    """
    # Given a parent session, ordered ambiguity, no harness or matches, and a harness
    # with no id.
    # When log show or its parent command runs.
    # Then the labels distinguish resolved, ambiguous and unknown sessions; time has
    # UTC milliseconds.
    pytest.skip("Pending log show implementation")


def test_latest_reviews() -> None:
    """AC-3 retains the latest review per judge and commit.

    The scenario exercises the report through the log command.
    """
    # Given human and agent reviews of one commit, a superseded review, and a second
    # commit.
    # When log show or its parent command runs.
    # Then the retained reviews follow event order; text shortens commits and JSON
    # retains full commits and citation order.
    pytest.skip("Pending log show implementation")


def test_mixed_rows() -> None:
    """AC-3 places a row by its latest context or review.

    The scenario exercises the report through the log command.
    """
    # Given a review-only gate, a context-only stage, and a gate with both kinds.
    # When log show or its parent command runs.
    # Then review-only rows have null context; mixed rows place by their review and
    # print context first.
    pytest.skip("Pending log show implementation")


def test_missing_inputs() -> None:
    """AC-4 handles absent Works, logs and repositories.

    The scenario exercises the report through the log command.
    """
    # Given an absent or empty log, an unmatched or retired Work, and an unavailable
    # repository.
    # When log show or its parent command runs.
    # Then retired Works are visible. No log or unmatched Work gives empty
    # text and {"works": {}, "skipped": 0} in JSON. No repository exits two.
    pytest.skip("Pending log show implementation")


def test_damaged_lines_and_files() -> None:
    """AC-5 counts bad lines and reads each file independently.

    The scenario exercises the report through the log command.
    """
    # Given a torn line at EOF, a higher version, invalid UTF-8 alone and inside valid
    # JSON.
    # When log show or its parent command runs.
    # Then only bad lines count, replacement text is shown, and the next file starts
    # cleanly.
    pytest.skip("Pending log show implementation")


def test_diagnostics_for_filtered_works() -> None:
    """AC-5 reports the global skip count.

    The scenario exercises the report through the log command.
    """
    # Given one bad line and events of two Works, then an entirely unreadable log.
    # When log show or its parent command runs.
    # Then filtering keeps the global count even when the JSON works map is
    # empty. Text has singular or plural notes and no note when skipped is zero.
    pytest.skip("Pending log show implementation")


def test_ordering() -> None:
    """AC-6 breaks ties by file and line and sorts Works by id.

    The scenario exercises the report through the log command.
    """
    # Given equal event times across files and within one file, with reversed listing
    # and Work order.
    # When log show or its parent command runs.
    # Then file name and line break ties, and Work ids are sorted.
    pytest.skip("Pending log show implementation")


def test_unreadable_listed_file() -> None:
    """AC-4 distinguishes an absent log directory from a failed file read.

    A listed file that vanishes or is unreadable is a command error.
    """
    # Given a log file that is listed but then raises OSError on read.
    # When log show runs in each output form.
    # Then it preserves the filesystem error as a diagnostic, exits two,
    # and emits no partial report.
    pytest.skip("Pending log show implementation")
