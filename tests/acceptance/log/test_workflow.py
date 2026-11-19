# SPDX-License-Identifier: Apache-2.0
"""Exercise the complete event log through the installed commands.

The scenarios record real reviews in isolated clones and inspect the report
or the files in each clone's Wio home.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox

_REVIEW = ["k3m9xq", "deliver", "architecture-review"]
_TRAILERS = ["trailers", *_REVIEW, "--result"]
_SHOW = ["log", "show", "--json", "k3m9xq"]


@pytest.fixture
def log_home(wio: Wio, sandbox: Sandbox) -> Path:
    """Prepare a reviewable repository and an empty Wio home.

    Args:
        wio: Creates the clone and its first commit.
        sandbox: Supplies the isolated Wio home.

    Returns:
        The empty Wio home for this command.
    """
    wio.fixture("trailers/command")
    wio.commit("feat: add the reviewed artifact")
    home = Path(sandbox.env["WIO_HOME"])
    home.mkdir()
    return home


def _events_path(home: Path) -> Path:
    """Find the only events file written by the clone.

    Args:
        home: The scenario's Wio home.

    Returns:
        The file written by the sink in the clone's log directory.
    """
    (path,) = (home / "log").glob("*/events.jsonl")
    return path


@pytest.mark.channels(Channel.CLI)
@pytest.mark.parametrize("result", ["pass", "maybe"])
def test_trailers_records_only_accepted_reviews(
    wio: Wio, log_home: Path, result: str
) -> None:
    """AC-1 shows the accepted review and leaves the log empty on refusal.

    Args:
        wio: Runs trailers and log show in the clone.
        log_home: An empty Wio home before the review.
        result: A configured result or a result that the checker refuses.
    """
    # Given a gate with a reviewable commit and citation AC-1.
    head = wio.driver.git(["rev-parse", "HEAD"]).stdout.strip()

    # When trailers checks and records the review.
    outcome = wio.run([*_TRAILERS, result, "--cite", "AC-1=pass"])

    # Then accepted reviews appear in show and refused reviews leave no files.
    if result == "maybe":
        assert outcome.exit_code == 1
        assert not list(log_home.iterdir())
        return
    assert outcome.exit_code == 0
    shown = wio.run(_SHOW)
    assert (shown.exit_code, shown.stderr) == (0, "")
    (row,) = json.loads(shown.stdout)["works"]["k3m9xq"]
    assert row["stage"] == "architecture-review"
    (review,) = row["reviews"]
    assert (review["result"], review["judge"], review["commit"], review["cited"]) == (
        "pass",
        "agent",
        head,
        {"AC-1": "pass"},
    )


@pytest.mark.channels(Channel.CLI)
def test_review_entry_points_append_the_same_payload(wio: Wio, log_home: Path) -> None:
    """AC-3 records the same review payload through either command.

    Args:
        wio: Runs both entry points against the same artifact.
        log_home: The home that receives both entries.
    """
    # Given the same failed review request for both forms.
    options = ["--result", "fail", "--cite", "AC-1=fail"]

    # When the review is recorded with trailers and then with log review.
    trailers = wio.run(["trailers", *_REVIEW, *options])
    review = wio.run(["log", "review", *_REVIEW, *options])

    # Then both write equal payloads and the log form does not print a record.
    assert (trailers.exit_code, review.exit_code, review.stdout) == (0, 0, "")
    first, second = map(json.loads, _events_path(log_home).read_bytes().splitlines())
    envelope = {"time", "directory", "harness", "session", "parent", "matches", "ids"}
    assert first["type"] == second["type"] == "review"
    first_payload = {key: value for key, value in first.items() if key not in envelope}
    second_payload = {
        key: value for key, value in second.items() if key not in envelope
    }
    assert first_payload == second_payload


@pytest.mark.channels(Channel.CLI)
@pytest.mark.parametrize("switch", ["off", "maybe"])
def test_log_switch_preserves_the_record(
    wio: Wio, sandbox: Sandbox, log_home: Path, switch: str
) -> None:
    """AC-4 controls writing without changing the printed gate record.

    Args:
        wio: Runs the recording command.
        sandbox: Supplies its environment.
        log_home: The initially empty Wio home.
        switch: The opt-out or an unrecognized value.
    """
    # Given the expected record from the baseline review in a separate home.
    baseline_home = log_home.with_name("baseline")
    sandbox.env["WIO_HOME"] = str(baseline_home)
    baseline = wio.run([*_TRAILERS, "pass"])
    sandbox.env.update(WIO_HOME=str(log_home), WIO_LOG=switch)

    # When the same review runs with the switch.
    outcome = wio.run([*_TRAILERS, "pass"])

    # Then stdout and exit code stay the same and the switch controls the log.
    assert (outcome.exit_code, baseline.exit_code, baseline.stderr) == (0, 0, "")
    assert outcome.stdout == baseline.stdout
    if switch == "off":
        assert outcome.stderr == ""
        assert not list(log_home.iterdir())
    else:
        assert outcome.stderr.startswith("warning: WIO_LOG ")
        (line,) = _events_path(log_home).read_bytes().splitlines()
        assert json.loads(line)["type"] == "review"


@pytest.mark.channels(Channel.CLI)
def test_show_reads_reviews_on_both_sides_of_damage(wio: Wio, log_home: Path) -> None:
    """AC-7 reads entries around torn and unsupported lines.

    Args:
        wio: Records two reviews and shows the damaged log.
        log_home: Supplies the log file to damage.
    """
    # Given two reviews of the same artifact by different judges.
    agent = wio.run([*_TRAILERS, "pass"])
    human = wio.run([*_TRAILERS, "fail", "--judge", "human"])
    assert (agent.exit_code, human.exit_code) == (0, 0)
    path = _events_path(log_home)
    first, second = path.read_bytes().splitlines(keepends=True)
    newer_event = json.loads(first)
    newer_event["v"] = 999
    newer_line = json.dumps(newer_event).encode() + b"\n"
    path.write_bytes(first + b'{"torn":\n' + newer_line + second)

    # When the report reads the damaged log.
    shown = wio.run(_SHOW)

    # Then it still contains both reviews and counts both damaged lines.
    assert (shown.exit_code, shown.stderr) == (0, "")
    report = json.loads(shown.stdout)
    assert report["skipped"] == 2
    (row,) = report["works"]["k3m9xq"]
    assert [(r["judge"], r["result"]) for r in row["reviews"]] == [
        ("agent", "pass"),
        ("human", "fail"),
    ]


@pytest.mark.channels(Channel.CLI)
def test_unconfigured_environment_values_stay_out_of_the_log(
    wio: Wio, sandbox: Sandbox, log_home: Path
) -> None:
    """AC-8 records configured IDs and excludes unrelated variables.

    Args:
        wio: Runs the real review command.
        sandbox: Supplies the configured and unrelated variables.
        log_home: The home to inspect after recording.
    """
    # Given a named harness session and an unrelated sentinel that fits ID syntax.
    unrelated_value = "unmapped-test-sentinel"
    sandbox.env.update(CLAUDE_CODE_SESSION_ID="c1", SECRET_TOKEN=unrelated_value)

    # When the review is recorded.
    outcome = wio.run([*_TRAILERS, "pass"])

    # Then only the harness variable is recorded, and no file has the sentinel.
    assert (outcome.exit_code, outcome.stderr) == (0, "")
    (line,) = _events_path(log_home).read_bytes().splitlines()
    assert json.loads(line)["ids"] == {"CLAUDE_CODE_SESSION_ID": "c1"}
    assert all(
        unrelated_value.encode() not in path.read_bytes()
        for path in log_home.rglob("*")
        if path.is_file()
    )
