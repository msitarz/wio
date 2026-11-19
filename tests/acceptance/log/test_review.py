# SPDX-License-Identifier: Apache-2.0
"""Contract scenarios for recording a review through the log command.

The scenarios compare both review entry points and observe the log on disk.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox


def test_both_commands_record_the_same_event() -> None:
    """AC-1 shares the reviewed commit, verdict and ordered citations.

    The tests inspect events written by each real command.
    """
    # Given k3m9xq deliver docs-review, a work commit under a pure gate commit,
    # and fail by human with citations AC-1=fail then AC-3=pass.
    # When log review and trailers run with the same options.
    # Then both write equal ReviewEvents and log review has empty stdout.
    pytest.skip("Pending log review implementation")


def test_review_outputs_silence_or_ordered_json() -> None:
    """AC-2 exposes the review payload to scripts.

    Both output forms still produce the same review event.
    """
    # Given k3m9xq deliver docs-review, reviewed commit of 40 a characters,
    # result fail, citations AC-1=fail then AC-3=pass and an omitted judge.
    # When log review runs with and without --json.
    # Then each exits zero. Text mode has empty stdout. JSON contains just
    # event, whose keys in order are work, action, stage, commit, judge, result,
    # cited and hashes. Values are k3m9xq, deliver, docs-review, the full reviewed
    # SHA, agent, fail, the ordered citation map, and an empty hashes map.
    pytest.skip("Pending log review implementation")


def test_warning_does_not_stop_a_review() -> None:
    """AC-3 preserves the stage-outside-pipeline warning.

    Comparison with trailers protects both diagnostic and event parity.
    """
    # Given system-review is a gate outside the Work's deliver pipeline.
    # When both commands review k3m9xq deliver system-review with result pass.
    # Then each exits zero with identical stderr and equal recorded events.
    pytest.skip("Pending log review implementation")


def test_field_and_citation_refusals_match_trailers() -> None:
    """AC-4 preserves field and citation diagnostics and writes no event.

    The comparison includes offending lines and the order of diagnostics.
    """
    # Given k3m9xq deliver docs-review with result pass unless overridden.
    # When both commands run for each case: result maybe, judge bogus,
    # stage nonesuch, Work nope99, cite AC-99=pass, duplicate AC-1=pass
    # and AC-1=fail, and unselected rule docs.DOC001=fail.
    # Then each exits 1 with empty stdout and identical stderr, and the
    # event sink receives nothing.
    pytest.skip("Pending log review implementation")


def test_review_refuses_a_history_with_no_reviewed_commit() -> None:
    """AC-4 reports the missing reviewed commit after the other checks pass.

    A history made solely of the gate's own commits provides no artifact.
    """
    # Given k3m9xq deliver docs-review and only pure gate commits.
    # When log review runs with result pass.
    # Then it exits 1 with empty stdout and no event, and stderr is exactly
    # 'error: Wio-Work: no reviewed commit was found' followed by a newline.
    pytest.skip("Pending log review implementation")


def test_review_stops_at_the_first_refusing_group_in_both_forms() -> None:
    """AC-4 refuses invalid fields before validating citations.

    JSON is generated only when the review passed all checks.
    """
    # Given result maybe and cite AC-99=pass in the same request.
    # When log review runs with and without --json.
    # Then both exit 1 with the same result diagnostic, no AC-99 diagnostic,
    # no stdout and no event.
    pytest.skip("Pending log review implementation")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
@pytest.mark.parametrize(
    "args",
    [
        ["k3m9xq", "deliver", "docs-review"],
        ["k3m9xq,other1", "deliver", "docs-review", "--result", "pass"],
        ["k3m9xq", "deliver", "docs-review", "--result", "pass", "--bogus"],
    ],
    ids=["missing-result", "work-list", "unknown-option"],
)
def test_usage_mistakes_exit_two(wio: Wio, sandbox: Sandbox, args: list[str]) -> None:
    """AC-5 distinguishes syntax errors from refused review fields.

    Args:
        wio: Runs the normal log command.
        sandbox: Supplies the isolated Wio home.
        args: The invalid arguments for review.
    """
    # Given an invalid review command and an untouched Wio home.
    home = Path(sandbox.env["WIO_HOME"])

    # When the command is parsed.
    output = wio.run(["log", "review", *args])

    # Then parsing exits two, explains the problem and writes no event.
    assert (output.exit_code, output.stdout) == (2, "")
    assert "error:" in output.stderr
    assert not home.exists()


def test_config_failure_matches_trailers() -> None:
    """AC-5 rejects invalid config before checking a review.

    Both commands load the same effective configuration.
    """
    # Given a real clone with an invalid config.
    # When both commands are called with a valid review request.
    # Then each exits 2 with identical stderr, empty stdout and no event.
    pytest.skip("Pending log review implementation")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_help_names_show_and_review(wio: Wio) -> None:
    """AC-6 makes review and show discoverable in a directory outside Git.

    Args:
        wio: Runs the command from an uninitialized sandbox.
    """
    # Given a working directory outside a repository.

    # When log help is requested.
    output = wio.run(["log", "-h"])

    # Then help names both forms and exits successfully.
    assert (output.exit_code, output.stderr) == (0, "")
    assert "show" in output.stdout
    assert "review" in output.stdout


def test_a_real_review_is_visible_in_show() -> None:
    """AC-7 records a review that the show command can read.

    The reviewed artifact and timestamp appear in the text report.
    """
    # Given a real clone, a reviewable Work commit and a fresh Wio home.
    # When log review records pass and log show selects that Work.
    # Then the review exits zero with empty stdout, and the Work's text
    # shows the action, gate, agent pass, 12-character SHA and event time.
    pytest.skip("Pending log review implementation")


def test_failed_and_disabled_logs_preserve_review_success() -> None:
    """AC-8 preserves command results when the sink cannot append.

    It covers a write failure and the switch that skips the sink's work.
    """
    # Given a real clone and a Wio home beneath a regular file, or a fresh
    # Wio home and WIO_LOG=off.
    # When log review records pass.
    # Then each exits zero with empty stdout. The first warns on stderr
    # that the event log could not be written. The second has empty stderr
    # and leaves its home directory empty.
    pytest.skip("Pending log review implementation")
