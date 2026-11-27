# SPDX-License-Identifier: Apache-2.0
"""Acceptance scenarios for recording a stage-entry `context` event."""

import json
from typing import TYPE_CHECKING, Any

import pytest

from tests.acceptance.channels import Channel
from tests.acceptance.drivers.in_process import (
    fixed_compiler,
    unavailable_temporary_directory,
)

if TYPE_CHECKING:
    from pathlib import Path

    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox

_ARGS = ["context", "k3m9xq", "deliver", "implementation"]


def _events(log_home: Path) -> list[dict[str, Any]]:
    """Read every recorded JSON event line under a Wio home directory.

    Args:
        log_home: The `$WIO_HOME` directory holding the clone's `events.jsonl`.

    Returns:
        The parsed JSON objects in file order, or an empty list if none exist.
    """
    files = list(log_home.rglob("events.jsonl"))
    if not files:
        return []
    (path,) = files
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


@pytest.mark.channels(Channel.IN_PROCESS)
def test_a_run_records_one_event_with_what_it_gave(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-1, AC-3: one run writes one event with ordered rules and no gate fields."""
    # Given a compiler result with two rules and a plain stage without gate = true
    wio.fixture("context/unreadable")
    log_home = tmp_path / "wio-home"
    sandbox.env["WIO_HOME"] = str(log_home)
    rules = {"mp.ARC001": "hash-arc001", "mp.ERR002": "hash-err002"}

    # When `wio context` runs
    with fixed_compiler("bundle body\n", 139, bundle_id="7a2383bc4098", rules=rules):
        result = wio.run(_ARGS)

    # Then the log holds one context event with matching metadata, ordered rules,
    # and neither `start` nor `dirty`
    assert (result.exit_code, result.stdout, result.stderr) == (0, "bundle body\n", "")
    (event,) = _events(log_home)
    assert event["type"] == "context"
    assert event["work"] == "k3m9xq"
    assert event["action"] == "deliver"
    assert event["stage"] == "implementation"
    assert event["bundle"] == "7a2383bc4098"
    assert event["size"] == 139
    assert event["rules"] == rules
    assert list(event["rules"]) == ["mp.ARC001", "mp.ERR002"]
    assert "start" not in event
    assert "dirty" not in event


@pytest.mark.channels(Channel.IN_PROCESS)
def test_a_result_with_no_rule_records_empty_rules(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-2: one rule records that rule, and no rules records an empty mapping."""
    # Given a compiler result with one rule and one with none
    wio.fixture("context/unreadable")
    log_home = tmp_path / "wio-home"
    sandbox.env["WIO_HOME"] = str(log_home)

    # When `wio context` runs for each
    with fixed_compiler("one\n", 10, bundle_id="111111111111", rules={"mp.A": "h1"}):
        first = wio.run(_ARGS)
    with fixed_compiler("none\n", 12, bundle_id="222222222222", rules={}):
        second = wio.run(_ARGS)

    # Then the first event holds that rule and the second has empty rules
    assert (first.exit_code, second.exit_code) == (0, 0)
    first_event, second_event = _events(log_home)
    assert first_event["rules"] == {"mp.A": "h1"}
    assert second_event["rules"] == {}


@pytest.mark.channels(Channel.CLI)
def test_a_failure_to_write_never_blocks(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-4: an unwritable log or unlocatable WIO_HOME warns, prints, and exits 0."""
    # Given a repository and first an unwritable events.jsonl, then a relative WIO_HOME
    wio.fixture("context/unreadable")
    log_home = tmp_path / "wio-home"
    sandbox.env["WIO_HOME"] = str(log_home)
    # Seed the log directory path, then replace events.jsonl with a directory so
    # appending fails on every platform.
    seed = wio.run(_ARGS)
    assert seed.exit_code == 0
    (events_file,) = list(log_home.rglob("events.jsonl"))
    events_file.unlink()
    events_file.mkdir()

    # When `wio context` runs with the unwritable log and then with a relative WIO_HOME
    unwritable = wio.run(_ARGS)
    sandbox.env["WIO_HOME"] = "relative/home"
    unlocatable = wio.run(_ARGS)

    # Then both warn appropriately, print the bundle, and exit 0
    assert unwritable.exit_code == 0
    assert unwritable.stdout == seed.stdout
    assert "warning: the event log could not be written:" in unwritable.stderr
    assert str(events_file) in unwritable.stderr

    assert unlocatable.exit_code == 0
    assert unlocatable.stdout == seed.stdout
    assert "warning: the event log could not be located:" in unlocatable.stderr


@pytest.mark.channels(Channel.IN_PROCESS)
def test_a_failed_delivery_records_no_event(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-5: a failed `--output` write or missing temp dir records no event."""
    # Given an unwritable output path and an unavailable temporary directory
    wio.fixture("context/unreadable")
    log_home = tmp_path / "wio-home"
    sandbox.env["WIO_HOME"] = str(log_home)
    sandbox.env.pop("TMPDIR", None)

    # When `wio context` runs for each failing delivery
    with fixed_compiler("bundle\n", 7):
        bad_path = wio.run([*_ARGS, "--output", "."])
    with fixed_compiler("bundle\n", 7), unavailable_temporary_directory():
        no_tmp = wio.run([*_ARGS, "--output"])

    # Then both fail with exit 2 and no event is written
    assert (bad_path.exit_code, bad_path.stdout) == (2, "")
    assert (no_tmp.exit_code, no_tmp.stdout) == (2, "")
    assert _events(log_home) == []


@pytest.mark.channels(Channel.IN_PROCESS)
def test_each_run_that_delivers_writes_its_own_event(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-6: a repeated run writes two events, and a warned run writes one."""
    # Given a repository and separate Wio homes for the two cases
    wio.fixture("context/unreadable")
    repeated_home = tmp_path / "repeated"
    warned_home = tmp_path / "warned"

    # When the stage runs twice in one home and once with a warning in the other
    sandbox.env["WIO_HOME"] = str(repeated_home)
    with fixed_compiler("bundle\n", 7, bundle_id="aaaaaaaaaaaa"):
        first = wio.run(_ARGS)
        second = wio.run(_ARGS)

    sandbox.env["WIO_HOME"] = str(warned_home)
    with fixed_compiler(
        "bundle\n", 7, bundle_id="bbbbbbbbbbbb", warnings=("a warning",)
    ):
        warned = wio.run(_ARGS)

    # Then the first leaves two events and the second writes one
    assert (first.exit_code, second.exit_code, warned.exit_code) == (0, 0, 0)
    assert len(_events(repeated_home)) == 2
    assert len(_events(warned_home)) == 1
    assert warned.stderr == "warning: a warning\n"


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_switched_off_log_writes_no_event(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-7: `WIO_LOG=off` prints the bundle, writes no event, and gives no warning."""
    # Given `WIO_LOG=off`
    wio.fixture("context/unreadable")
    log_home = tmp_path / "wio-home"
    sandbox.env["WIO_HOME"] = str(log_home)
    sandbox.env["WIO_LOG"] = "off"

    # When `wio context` runs
    result = wio.run(_ARGS)

    # Then the bundle is printed, no event is written, and no warning is reported
    assert result.exit_code == 0
    assert result.stdout != ""
    assert result.stderr == ""
    assert _events(log_home) == []
