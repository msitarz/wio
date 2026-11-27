# SPDX-License-Identifier: Apache-2.0
"""Acceptance scenarios for recording where a gate review starts."""

from typing import TYPE_CHECKING
from unittest import mock

import pytest

from tests.acceptance.channels import Channel
from tests.acceptance.context.test_stage_entry import read_events
from tests.acceptance.drivers.in_process import fixed_compiler

if TYPE_CHECKING:
    from pathlib import Path

    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox

_EXTRA_CONFIG = """
[actions.define]
description = "Define"

[stages.review]
goal = "Review"
gate = true

[stages.review-contract]
goal = "Review contract"
gate = true
"""

_GATE_ARGS = ["context", "k3m9xq", "deliver", "review"]


def _setup_repo(wio: Wio, sandbox: Sandbox, log_home: Path) -> None:
    """Create a minimal project with a gate stage and isolated WIO_HOME.

    Args:
        wio: The scenario's facade.
        sandbox: The scenario's sandbox.
        log_home: Directory for `$WIO_HOME`.
    """
    wio.fixture("context/unreadable")
    base = wio.read(".agents/wio/config.toml").decode("utf-8")
    wio.put(".agents/wio/config.toml", (base + _EXTRA_CONFIG).encode("utf-8"))
    sandbox.env["WIO_HOME"] = str(log_home)


def _head(wio: Wio) -> str:
    """Return the full commit id of `HEAD`.

    Args:
        wio: The scenario's facade.

    Returns:
        The 40-character commit id of `HEAD`.
    """
    return wio.driver.git(["rev-parse", "HEAD"]).stdout.strip()


@pytest.mark.channels(Channel.CLI)
def test_a_gate_records_the_commit_its_review_starts_from(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-1: start skips pure gate commits but stops at mixed or none commits."""
    # Given a history with a base commit under two pure gate commits
    log_home = tmp_path / "wio-home"
    _setup_repo(wio, sandbox, log_home)
    wio.commit(
        "feat: base\n\nWio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: implementation"
    )
    base_sha = _head(wio)
    gate_msg = (
        "chore: gate\n\nWio-Work: k3m9xq\nWio-Action: deliver\n"
        "Wio-Stage: review\nWio-Result: pass\nWio-Judge: agent"
    )
    wio.commit(gate_msg, empty=True)
    wio.commit(gate_msg, empty=True)

    # When `wio context` runs for the gate, then after a mixed commit and a none commit
    first = wio.run(_GATE_ARGS)
    mixed_msg = (
        "chore: mixed\n\nWio-Work: k3m9xq\nWio-Action: deliver\n"
        "Wio-Stage: implementation\n\nWio-Work: k3m9xq\nWio-Action: deliver\n"
        "Wio-Stage: review\nWio-Result: pass\nWio-Judge: agent"
    )
    wio.commit(mixed_msg, empty=True)
    mixed_sha = _head(wio)
    second = wio.run(_GATE_ARGS)
    wio.commit("chore: misc\n\nWio-Work: none", empty=True)
    none_sha = _head(wio)
    third = wio.run(_GATE_ARGS)

    # Then each event's start is the expected full commit id
    assert (first.exit_code, second.exit_code, third.exit_code) == (0, 0, 0)
    ev1, ev2, ev3 = read_events(log_home)
    assert (ev1["start"], ev2["start"], ev3["start"]) == (base_sha, mixed_sha, none_sha)


@pytest.mark.channels(Channel.CLI)
def test_a_gate_records_dirty_before_delivering_to_worktree(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-2: dirty is false when clean or writing inside worktree, true when dirty."""
    # Given a clean repository
    log_home = tmp_path / "wio-home"
    _setup_repo(wio, sandbox, log_home)
    wio.commit("feat: init\n\nWio-Work: none")

    # When the gate runs clean, then with `--output` inside the worktree, then dirty
    clean = wio.run(_GATE_ARGS)
    inside = wio.run([*_GATE_ARGS, "--output", "bundle.md"])
    dirty = wio.run(_GATE_ARGS)

    # Then clean and inside-output record dirty=False, and the third records dirty=True
    assert (clean.exit_code, inside.exit_code, dirty.exit_code) == (0, 0, 0)
    ev_clean, ev_inside, ev_dirty = read_events(log_home)
    assert (ev_clean["dirty"], ev_inside["dirty"], ev_dirty["dirty"]) == (
        False,
        False,
        True,
    )


@pytest.mark.channels(Channel.CLI)
def test_a_history_with_nothing_to_review_records_no_start(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-3: an empty repo and a pure-gate-only repo record no start and exit 0."""
    # Given an empty repository with untracked Work files
    empty_home = tmp_path / "empty-home"
    _setup_repo(wio, sandbox, empty_home)

    # When the gate runs empty, then after a pure-gate-only commit
    empty_run = wio.run(_GATE_ARGS)
    gate_home = tmp_path / "gate-home"
    sandbox.env["WIO_HOME"] = str(gate_home)
    wio.commit(
        "chore: gate\n\nWio-Work: k3m9xq\nWio-Action: deliver\n"
        "Wio-Stage: review\nWio-Result: pass\nWio-Judge: agent"
    )
    gate_only_run = wio.run(_GATE_ARGS)

    # Then neither event has `start`, empty repo has `dirty=True`, and both exit 0
    assert (empty_run.exit_code, gate_only_run.exit_code) == (0, 0)
    (ev_empty,) = read_events(empty_home)
    (ev_gate_only,) = read_events(gate_home)
    assert "start" not in ev_empty
    assert ev_empty["dirty"] is True
    assert "start" not in ev_gate_only


@pytest.mark.channels(Channel.CLI)
def test_a_review_in_an_empty_repository_is_refused_by_both_commands(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-5: `wio trailers --result` and `wio log review` exit 1 with no event."""
    # Given a repository with no commit and a Work in the working tree
    log_home = tmp_path / "wio-home"
    _setup_repo(wio, sandbox, log_home)

    # When `wio trailers --result` and `wio log review` run
    trailers = wio.run(
        ["trailers", "k3m9xq", "define", "review-contract", "--result", "pass"]
    )
    log_review = wio.run(
        ["log", "review", "k3m9xq", "define", "review-contract", "--result", "pass"]
    )

    # Then both exit 1, say no reviewed commit was found, and write no event
    assert (trailers.exit_code, log_review.exit_code) == (1, 1)
    assert "no reviewed commit" in trailers.stderr.lower()
    assert "no reviewed commit" in log_review.stderr.lower()
    assert read_events(log_home) == []


@pytest.mark.channels(Channel.IN_PROCESS)
def test_a_failed_read_drops_only_what_failed(
    wio: Wio, sandbox: Sandbox, tmp_path: Path
) -> None:
    """AC-6: failing history or repository drops only that field, warns, and exits 0."""
    # Given a gate stage and isolated WIO_HOME
    log_home = tmp_path / "wio-home"
    _setup_repo(wio, sandbox, log_home)

    # When history fails, then repository fails with RuntimeError and ValueError
    with (
        fixed_compiler("bundle\n", 7),
        mock.patch(
            "wio.cli.table._ContextReviewedCommit.find",
            side_effect=ValueError("bad history"),
        ),
        mock.patch(
            "tests.acceptance.drivers.in_process.SandboxRepository.is_dirty",
            return_value=True,
        ),
    ):
        bad_history = wio.run(_GATE_ARGS)

    with (
        fixed_compiler("bundle\n", 7),
        mock.patch(
            "wio.cli.table._ContextReviewedCommit.find",
            return_value="a" * 40,
        ),
        mock.patch(
            "tests.acceptance.drivers.in_process.SandboxRepository.is_dirty",
            side_effect=RuntimeError("no repo"),
        ),
    ):
        bad_repo_rt = wio.run(_GATE_ARGS)

    with (
        fixed_compiler("bundle\n", 7),
        mock.patch(
            "wio.cli.table._ContextReviewedCommit.find",
            return_value="b" * 40,
        ),
        mock.patch(
            "tests.acceptance.drivers.in_process.SandboxRepository.is_dirty",
            side_effect=ValueError("status failed"),
        ),
    ):
        bad_repo_val = wio.run(_GATE_ARGS)

    # Then each warns naming `start` or `dirty`, prints the bundle, exits 0,
    # and drops only the field that failed
    assert (
        bad_history.exit_code,
        bad_repo_rt.exit_code,
        bad_repo_val.exit_code,
    ) == (0, 0, 0)
    assert (bad_history.stdout, bad_repo_rt.stdout, bad_repo_val.stdout) == (
        "bundle\n",
        "bundle\n",
        "bundle\n",
    )
    assert "start" in bad_history.stderr
    assert "dirty" in bad_repo_rt.stderr
    assert "dirty" in bad_repo_val.stderr
    ev_hist, ev_rt, ev_val = read_events(log_home)
    assert "start" not in ev_hist
    assert ev_hist["dirty"] is True
    assert ev_rt["start"] == "a" * 40
    assert "dirty" not in ev_rt
    assert ev_val["start"] == "b" * 40
    assert "dirty" not in ev_val
