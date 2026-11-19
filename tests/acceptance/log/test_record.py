# SPDX-License-Identifier: Apache-2.0
"""System scenarios for the real review command and log sink.

Each case records a review through the CLI and inspects the single event in
an isolated Wio home.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox

_CONFIG = ".agents/wio/config.toml"
_NESTED = {"CLAUDE_CODE_SESSION_ID": "c1", "CODEX_THREAD_ID": "t2"}
_PREFER_CODEX = '[log]\nprefer_harness = ["codex"]'
_CURSOR = '[log.harnesses.cursor]\nsession = ["CURSOR_TRACE_ID"]'


def _record_review(
    wio: Wio, sandbox: Sandbox, variables: dict[str, str], settings: str = ""
) -> dict[str, object]:
    """Record one gate result from a real clone with a fresh log.

    Args:
        wio: The CLI facade, which initializes and commits the gate fixture.
        sandbox: The isolated environment of the command.
        variables: The mapped variables and any preference override for this run.
        settings: Extra config for the log, or an empty string for defaults.

    Returns:
        The wire fields of the only review event.

    Raises:
        AssertionError: The command failed or did not record exactly one review.
    """
    wio.fixture("trailers/command")
    if settings:
        wio.put(_CONFIG, wio.read(_CONFIG) + f"\n{settings}\n".encode())
    wio.commit("feat: add the reviewable Work")
    sandbox.env.update(variables)
    home = Path(sandbox.env["WIO_HOME"])
    home.mkdir()
    outcome = wio.run(
        ["trailers", "k3m9xq", "deliver", "architecture-review", "--result", "pass"]
    )
    assert (outcome.exit_code, outcome.stderr) == (0, "")
    assert "Wio-Result: pass\n" in outcome.stdout
    (events,) = (home / "log").glob("*/events.jsonl")
    (line,) = events.read_bytes().splitlines()
    event: dict[str, object] = json.loads(line)
    assert event["type"] == "review"
    return event


@pytest.mark.channels(Channel.CLI)
@pytest.mark.parametrize(
    ("variables", "harness", "session", "parent"),
    [
        (
            {"CLAUDE_CODE_SESSION_ID": "c1", "AI_AGENT": "claude-code_2"},
            "claude-code",
            "c1",
            None,
        ),
        (
            {"CODEX_SESSION_ID": "s1", "CODEX_THREAD_ID": "t2"},
            "codex",
            "t2",
            "s1",
        ),
    ],
    ids=["claude-code", "codex-subagent"],
)
def test_real_review_carries_the_harness_session(
    wio: Wio,
    sandbox: Sandbox,
    variables: dict[str, str],
    harness: str,
    session: str,
    parent: str | None,
) -> None:
    """AC-1 stamps a real review with the harness session.

    Args:
        wio: Runs the review command in the clone.
        sandbox: Supplies the isolated environment and Wio home.
        variables: The harness variables for this run.
        harness: The expected harness name.
        session: The expected session id.
        parent: The expected parent id, if present.
    """
    # Given only the variables of one harness and a gate ready for review.

    # When the command records a review.
    event = _record_review(wio, sandbox, variables)

    # Then the stamp contains the session and the ids supplied by that harness.
    assert (event["harness"], event["session"], event.get("parent")) == (
        harness,
        session,
        parent,
    )
    assert event["ids"] == variables
    assert event["matches"] == [harness]


@pytest.mark.channels(Channel.CLI)
@pytest.mark.parametrize(
    ("settings", "variables", "harness", "session"),
    [
        (_CURSOR, {"CURSOR_TRACE_ID": "r9"}, "cursor", "r9"),
        (_PREFER_CODEX, _NESTED, "codex", "t2"),
        (
            _PREFER_CODEX,
            _NESTED | {"WIO_PREFER_HARNESS": "claude-code"},
            "claude-code",
            "c1",
        ),
    ],
    ids=["configured-harness", "config-preference", "environment-override"],
)
def test_log_settings_control_what_the_stamp_holds(
    wio: Wio,
    sandbox: Sandbox,
    settings: str,
    variables: dict[str, str],
    harness: str,
    session: str,
) -> None:
    """AC-2 applies configured mappings and preferences to the recorded session.

    Args:
        wio: Runs the review command in the clone.
        sandbox: Supplies the isolated environment and Wio home.
        settings: The additional log config.
        variables: The harness variables and any override for this case.
        harness: The expected harness name.
        session: The expected session id.
    """
    # Given a custom harness or a nested run with a config or env preference.

    # When the command records a review.
    event = _record_review(wio, sandbox, variables, settings)

    # Then the chosen session follows the effective config and override.
    assert (event["harness"], event["session"]) == (harness, session)
    assert event["ids"] == {
        name: value for name, value in variables.items() if name != "WIO_PREFER_HARNESS"
    }


@pytest.mark.channels(Channel.CLI)
@pytest.mark.parametrize(
    ("settings", "variables"),
    [
        ("", _NESTED),
        (_PREFER_CODEX, _NESTED | {"WIO_PREFER_HARNESS": "none"}),
    ],
    ids=["no-preference", "cleared-preference"],
)
def test_ambiguous_nested_review_preserves_both_matches(
    wio: Wio,
    sandbox: Sandbox,
    settings: str,
    variables: dict[str, str],
) -> None:
    """AC-3 records both matches for an unresolved nested run.

    Args:
        wio: Runs the review command in the clone.
        sandbox: Supplies the isolated environment and Wio home.
        settings: The log config for this case.
        variables: The nested harness variables and any preference override.
    """
    # Given two harnesses and a preference that is absent or cleared.

    # When the command records a review.
    event = _record_review(wio, sandbox, variables, settings)

    # Then it keeps both ordered matches and leaves the session unresolved.
    assert {"harness", "session", "parent"}.isdisjoint(event)
    assert event["matches"] == ["claude-code", "codex"]
    assert event["ids"] == _NESTED
