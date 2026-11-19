# SPDX-License-Identifier: Apache-2.0
"""Contract scenarios for recording a review through the log command.

The scenarios compare both review entry points and observe the log on disk.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox

_WORK = "k3m9xq"
_GATE_ARGS = [_WORK, "deliver", "docs-review"]
_LOG = ["log", "review"]
_TRAILERS = ["trailers"]
_CITES = ["--cite", "AC-1=fail", "--cite", "AC-3=pass"]
_CONFIG = ".agents/wio/config.toml"
_DESCRIPTION = ".agents/wio/works/k3m9xq/README.md"
_TEMPLATE = ".agents/wio/templates/t.leaf.md"
_GATE = (
    "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: docs-review\n"
    "Wio-Result: pass\nWio-Judge: agent"
)
_PAYLOAD_KEYS = (
    "work",
    "action",
    "stage",
    "commit",
    "judge",
    "result",
    "cited",
    "hashes",
)


def _project(wio: Wio) -> None:
    """Install the gate fixture with the cases needed for review comparisons.

    Args:
        wio: The facade used to build a real Git repository.
    """
    wio.fixture("trailers/command")
    config = wio.read(_CONFIG).replace(b"architecture-review", b"docs-review")
    wio.put(
        _CONFIG,
        config
        + b'\n[stages.system-review]\ngate = true\ngoal = "Review the system."\n',
    )
    wio.put(
        _TEMPLATE, wio.read(_TEMPLATE).replace(b"architecture-review", b"docs-review")
    )
    wio.put(
        _DESCRIPTION, wio.read(_DESCRIPTION) + b"\n### **AC-3** Another criterion\n"
    )


@pytest.fixture
def artifact(wio: Wio) -> str:
    """Build a history with a reviewable artifact under a pure gate commit.

    Args:
        wio: The facade used to build the history.

    Returns:
        The full commit id of the artifact.
    """
    _project(wio)
    wio.commit("feat: add the reviewable Work")
    head = wio.driver.git(["rev-parse", "HEAD"])
    assert head.exit_code == 0
    wio.commit(f"test: record a gate\n\n{_GATE}", empty=True)
    return head.stdout.strip()


def _home(sandbox: Sandbox) -> Path:
    """Get the isolated Wio home allocated to the scenario.

    Args:
        sandbox: The test process's isolated configuration.

    Returns:
        The path where events would be stored.
    """
    return Path(sandbox.env["WIO_HOME"])


def _events(sandbox: Sandbox) -> list[dict[str, object]]:
    """Read the event objects written by the two real commands.

    Args:
        sandbox: Supplies the Wio home that the commands used.

    Returns:
        The recorded event objects in append order.
    """
    paths = list((_home(sandbox) / "log").glob("*/events.jsonl"))
    (path,) = paths
    return [json.loads(line) for line in path.read_bytes().splitlines()]


def _payload(event: dict[str, object]) -> dict[str, object]:
    """Take the review fields from an event that also carries an envelope.

    Args:
        event: The event as read from the file.

    Returns:
        The review's fields, excluding the envelope and framing fields.
    """
    return {key: event[key] for key in _PAYLOAD_KEYS}


@pytest.mark.channels(Channel.CLI)
def test_both_commands_record_the_same_event(
    wio: Wio,
    sandbox: Sandbox,
    artifact: str,
) -> None:
    """AC-1 shares the reviewed commit, verdict and ordered citations.

    Args:
        wio: Runs the two commands on the same clone.
        sandbox: Supplies their isolated Wio home.
        artifact: The commit that both commands should review.
    """
    # Given identical review fields in a clone with a reviewable artifact.
    args = [*_GATE_ARGS, "--result", "fail", "--judge", "human", *_CITES]

    # When both forms record that review.
    logged = wio.run([*_LOG, *args])
    printed = wio.run([*_TRAILERS, *args])

    # Then both record the same event and only trailers prints a record.
    assert (logged.exit_code, logged.stdout, logged.stderr) == (0, "", "")
    assert (printed.exit_code, printed.stderr) == (0, "")
    assert "Wio-Result: fail\n" in printed.stdout
    first, second = _events(sandbox)
    assert first["type"] == second["type"] == "review"
    assert first["commit"] == second["commit"] == artifact
    assert _payload(first) == _payload(second)


@pytest.mark.channels(Channel.CLI)
def test_review_outputs_silence_or_ordered_json(
    wio: Wio,
    sandbox: Sandbox,
    artifact: str,
) -> None:
    """AC-2 returns exactly the event for the JSON form.

    Args:
        wio: Runs both output forms of the review command.
        sandbox: Supplies their isolated Wio home.
        artifact: The commit that the review should judge.
    """
    # Given two citations and no explicit judge.
    args = [*_LOG, *_GATE_ARGS, "--result", "fail", *_CITES]

    # When review runs with and without JSON output.
    text = wio.run(args)
    document = wio.run([*args, "--json"])

    # Then text is silent and JSON contains the full ordered payload.
    assert (text.exit_code, text.stdout, text.stderr) == (0, "", "")
    assert (document.exit_code, document.stderr) == (0, "")
    value = json.loads(document.stdout)
    assert list(value) == ["event"]
    assert tuple(value["event"]) == _PAYLOAD_KEYS
    assert tuple(value["event"]["cited"]) == ("AC-1", "AC-3")
    assert value == {
        "event": {
            "work": _WORK,
            "action": "deliver",
            "stage": "docs-review",
            "commit": artifact,
            "judge": "agent",
            "result": "fail",
            "cited": {"AC-1": "fail", "AC-3": "pass"},
            "hashes": {},
        }
    }
    first, second = _events(sandbox)
    assert _payload(first) == _payload(second) == value["event"]


@pytest.mark.channels(Channel.CLI)
@pytest.mark.usefixtures("artifact")
def test_warning_does_not_stop_a_review(wio: Wio, sandbox: Sandbox) -> None:
    """AC-3 preserves the warning for a gate outside the Work pipeline.

    Args:
        wio: Runs the two commands in the same repository.
        sandbox: Supplies the isolated Wio home.
    """
    # Given a configured gate outside the Work's pipeline.
    args = [_WORK, "deliver", "system-review", "--result", "pass"]

    # When both commands record the result.
    logged = wio.run([*_LOG, *args])
    printed = wio.run([*_TRAILERS, *args])

    # Then both warn and succeed, and the sink records equal reviews.
    assert (logged.exit_code, printed.exit_code, logged.stdout) == (0, 0, "")
    assert logged.stderr == printed.stderr
    assert logged.stderr.startswith("warning: Wio-Stage:")
    first, second = _events(sandbox)
    assert _payload(first) == _payload(second)


@pytest.mark.channels(Channel.CLI)
@pytest.mark.usefixtures("artifact")
@pytest.mark.parametrize(
    "args",
    [
        [*_GATE_ARGS, "--result", "maybe"],
        [*_GATE_ARGS, "--result", "pass", "--judge", "bogus"],
        [_WORK, "deliver", "nonesuch", "--result", "pass"],
        ["nope99", "deliver", "docs-review", "--result", "pass"],
        [*_GATE_ARGS, "--result", "pass", "--cite", "AC-99=pass"],
        [*_GATE_ARGS, "--result", "pass", "--cite", "AC-1=pass", "--cite", "AC-1=fail"],
        [*_GATE_ARGS, "--result", "pass", "--cite", "docs.DOC001=fail"],
        [_WORK, "deliver", "system-review", "--result", "pass", "--cite", "AC-99=pass"],
    ],
    ids=[
        "result",
        "judge",
        "stage",
        "work",
        "unrecognized-cite",
        "duplicate-cite",
        "unselected-rule",
        "warning-before-cite-error",
    ],
)
def test_field_and_citation_refusals_match_trailers(
    wio: Wio,
    sandbox: Sandbox,
    args: list[str],
) -> None:
    """AC-4 preserves the order and text of refusal diagnostics.

    Args:
        wio: Runs the two forms over the same configuration and history.
        sandbox: Supplies the isolated Wio home.
        args: A request that the shared checks should refuse.
    """
    # Given a review request with an invalid field or citation.

    # When both forms check the request.
    logged = wio.run([*_LOG, *args])
    printed = wio.run([*_TRAILERS, *args])

    # Then both refuse with identical stderr, empty stdout and no event.
    assert (logged.exit_code, printed.exit_code) == (1, 1)
    assert logged.stdout == printed.stdout == ""
    assert logged.stderr == printed.stderr
    assert "error:" in logged.stderr
    assert not _home(sandbox).exists()


@pytest.mark.channels(Channel.CLI)
def test_review_refuses_a_history_with_no_reviewed_commit(
    wio: Wio, sandbox: Sandbox
) -> None:
    """AC-4 refuses a history made solely of the gate's own commits.

    Args:
        wio: Builds the history and runs the log form.
        sandbox: Supplies the isolated Wio home.
    """
    # Given a repository with only pure gate commits.
    _project(wio)
    wio.commit(f"test: record only the gate\n\n{_GATE}")

    # When log review asks for the gate it judged.
    outcome = wio.run([*_LOG, *_GATE_ARGS, "--result", "pass"])

    # Then the missing-artifact error is reported and nothing is logged.
    assert (outcome.exit_code, outcome.stdout) == (1, "")
    assert outcome.stderr == "error: Wio-Work: no reviewed commit was found\n"
    assert not _home(sandbox).exists()


@pytest.mark.channels(Channel.CLI)
@pytest.mark.usefixtures("artifact")
def test_review_stops_at_the_first_refusing_group_in_both_forms(
    wio: Wio,
    sandbox: Sandbox,
) -> None:
    """AC-4 refuses invalid fields before checking citations or output mode.

    Args:
        wio: Runs both output forms on the same repository.
        sandbox: Supplies the isolated Wio home.
    """
    # Given a review with both a bad result and a bad citation.
    args = [*_LOG, *_GATE_ARGS, "--result", "maybe", "--cite", "AC-99=pass"]

    # When both output forms run.
    text = wio.run(args)
    document = wio.run([*args, "--json"])

    # Then each stops at the invalid result and sends nothing to the sink.
    assert (text.exit_code, document.exit_code, text.stdout, document.stdout) == (
        1,
        1,
        "",
        "",
    )
    assert text.stderr == document.stderr
    assert "Wio-Result" in text.stderr
    assert "AC-99" not in text.stderr
    assert not _home(sandbox).exists()


@pytest.mark.channels(Channel.CLI)
def test_review_refuses_none_as_a_work(wio: Wio, sandbox: Sandbox) -> None:
    """The log form checks none as an invalid Work for a gate review.

    Args:
        wio: Initializes a repository and runs the review.
        sandbox: Supplies the isolated Wio home.
    """
    # Given a repository whose Work is k3m9xq.
    _project(wio)

    # When the review request names the reserved Work value.
    outcome = wio.run([*_LOG, "none", "deliver", "docs-review", "--result", "pass"])

    # Then the fields are refused before accessing history or the event sink.
    assert (outcome.exit_code, outcome.stdout) == (1, "")
    assert "Wio-Work: none" in outcome.stderr
    assert not _home(sandbox).exists()


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


@pytest.mark.channels(Channel.CLI)
def test_review_outside_a_repository_is_a_usage_error(
    wio: Wio,
    sandbox: Sandbox,
) -> None:
    """AC-5 requires a repository before checking any review.

    Args:
        wio: The facade in a directory outside any repository.
        sandbox: Supplies the isolated Wio home.
    """
    # Given a working directory outside a repository.

    # When log review is invoked with valid syntax.
    outcome = wio.run([*_LOG, *_GATE_ARGS, "--result", "pass"])

    # Then repository discovery fails with code two and leaves the log alone.
    assert (outcome.exit_code, outcome.stdout) == (2, "")
    assert "not inside a git repository" in outcome.stderr
    assert not _home(sandbox).exists()


@pytest.mark.channels(Channel.CLI)
def test_config_failure_matches_trailers(wio: Wio, sandbox: Sandbox) -> None:
    """AC-5 exposes the same invalid config for both forms.

    Args:
        wio: Builds the repository and runs the two forms.
        sandbox: Supplies the isolated Wio home.
    """
    # Given a real repository with a config that cannot be parsed.
    _project(wio)
    wio.put(_CONFIG, b"[unfinished\n")
    args = [*_GATE_ARGS, "--result", "pass"]

    # When both commands run.
    logged = wio.run([*_LOG, *args])
    printed = wio.run([*_TRAILERS, *args])

    # Then both report the same error before producing anything.
    assert (logged.exit_code, printed.exit_code) == (2, 2)
    assert logged.stdout == printed.stdout == ""
    assert logged.stderr == printed.stderr
    assert _CONFIG in logged.stderr
    assert not _home(sandbox).exists()


@pytest.mark.channels(Channel.CLI)
def test_a_real_review_is_visible_in_show(
    wio: Wio,
    sandbox: Sandbox,
    artifact: str,
) -> None:
    """AC-7 records a review that the show command can read.

    Args:
        wio: Runs both real log commands.
        sandbox: Supplies the isolated Wio home.
        artifact: The work commit that the review should reference.
    """
    # Given a reviewable commit and an empty Wio home.
    _home(sandbox).mkdir()

    # When review records the result and show reads it.
    review = wio.run([*_LOG, *_GATE_ARGS, "--result", "pass"])
    show = wio.run(["log", "show", _WORK])

    # Then the resulting event is visible with the recorded time.
    assert (review.exit_code, review.stdout, review.stderr) == (0, "", "")
    assert (show.exit_code, show.stderr) == (0, "")
    (event,) = _events(sandbox)
    assert show.stdout == (
        f"{_WORK}\n  deliver docs-review  agent pass {artifact[:12]}  {event['time']}\n"
    )


@pytest.mark.channels(Channel.CLI)
@pytest.mark.usefixtures("artifact")
@pytest.mark.parametrize("mode", ["unwritable", "off"])
def test_failed_and_disabled_logs_preserve_review_success(
    wio: Wio,
    sandbox: Sandbox,
    mode: str,
) -> None:
    """AC-8 keeps command success when recording fails or is disabled.

    Args:
        wio: Runs a review that the checker accepts.
        sandbox: Supplies the isolated environment and Wio home.
        mode: Indicates a blocked Wio home or an explicit opt-out.
    """
    # Given a sink that cannot write or is switched off.
    home = _home(sandbox)
    if mode == "unwritable":
        home.touch()
        sandbox.env["WIO_HOME"] = str(home / "blocked")
    else:
        home.mkdir()
        sandbox.env["WIO_LOG"] = "off"

    # When the review runs.
    outcome = wio.run([*_LOG, *_GATE_ARGS, "--result", "pass"])

    # Then the command succeeds and any warning describes the write failure.
    assert (outcome.exit_code, outcome.stdout) == (0, "")
    if mode == "unwritable":
        assert outcome.stderr.startswith("warning: the event log could not be written:")
    else:
        assert outcome.stderr == ""
        assert not list(home.iterdir())
