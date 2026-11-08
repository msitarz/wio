# SPDX-License-Identifier: Apache-2.0
"""Tests for `GitRepository`, the adapter of the `Repository` port, without git."""

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.fakes import FakeEnvironment
from wio.io import adapters

if TYPE_CHECKING:
    from wio.env.ports import Environment
    from wio.io.ports import Repository


def _wired(environment: Environment | None = None) -> Repository:
    """Wire the adapter where the port is expected.

    Args:
        environment: Where the working directory comes from; a fake that
            reports `/r` by default.

    Returns:
        A `GitRepository`, which type checking accepts as a `Repository`.
    """
    return adapters.GitRepository(environment or FakeEnvironment(Path("/r")))


def _fake_run(
    monkeypatch: pytest.MonkeyPatch, result: subprocess.CompletedProcess[str]
) -> list[list[str]]:
    """Replace the subprocess call of the adapter with a recorded answer.

    Args:
        monkeypatch: The test's monkeypatch fixture.
        result: What the replaced call returns.

    Returns:
        The list that collects the command of each call.
    """
    calls: list[list[str]] = []

    def run(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return result

    monkeypatch.setattr(subprocess, "run", run)
    return calls


def test_root_and_identity_ask_the_commands_the_contract_names(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC-3: the adapter asks `rev-parse` for the top and the common directory."""
    # Given a git that answers with a path
    done = subprocess.CompletedProcess([], 0, stdout="/r/.git\n", stderr="")
    calls = _fake_run(monkeypatch, done)

    # When root and identity run
    repository = _wired(FakeEnvironment(tmp_path))
    root, identity = repository.root(), repository.identity()

    # Then both read the printed path and ask the commands the contract names
    assert (root, identity) == (Path("/r/.git"), Path("/r/.git"))
    assert calls == [
        ["git", "rev-parse", "--show-toplevel"],
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
    ]


def test_a_directory_outside_a_repository_says_so_and_what_to_do(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC-3: the message names the directory, the problem and the next step."""
    # Given a git that rejects the directory
    _fake_run(monkeypatch, subprocess.CompletedProcess([], 128, "", "fatal: no"))
    repository = _wired(FakeEnvironment(tmp_path))

    # When root runs
    with pytest.raises(RuntimeError) as caught:
        repository.root()

    # Then the message names the directory, says it is in no repository and says
    # to run wio from inside one
    message = str(caught.value)
    assert str(tmp_path) in message
    assert "not inside a git repository" in message
    assert "inside the repository" in message


def test_a_git_that_cannot_be_run_says_so_and_what_to_do(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC-3: a missing git is reported as that, not as a missing directory."""

    # Given a directory that exists and a git that cannot be started
    def missing(*_: object, **__: object) -> None:
        raise FileNotFoundError(2, "No such file or directory", "git")

    monkeypatch.setattr(subprocess, "run", missing)
    repository = _wired(FakeEnvironment(tmp_path))

    # When root runs
    with pytest.raises(RuntimeError) as caught:
        repository.root()

    # Then the message says git cannot be run and asks for it to be installed
    message = str(caught.value)
    assert "cannot run git" in message
    assert "git is installed" in message
    assert "PosixPath" not in message


def test_the_members_trailers_owns_name_the_trailers_work() -> None:
    """AC-4: show_index and is_dirty say which Work implements them."""
    # Given a GitRepository
    repository = _wired()

    # When show_index and is_dirty run
    # Then each raises NotImplementedError naming the trailers Work
    with pytest.raises(NotImplementedError, match="trailers Work"):
        repository.show_index(Path("f"))
    with pytest.raises(NotImplementedError, match="trailers Work"):
        repository.is_dirty()


def test_git_runs_in_the_directory_the_environment_reports(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC-3: the directory is handed to git as its working directory."""
    # Given a git that records how it is run, and an environment's directory
    seen: list[object] = []
    done = subprocess.CompletedProcess([], 0, stdout="/r\n", stderr="")

    def run(_command: list[str], **options: object) -> subprocess.CompletedProcess[str]:
        seen.append(options.get("cwd"))
        return done

    monkeypatch.setattr(subprocess, "run", run)
    repository = _wired(FakeEnvironment(tmp_path))

    # When root runs
    repository.root()

    # Then git was run in that directory
    assert seen == [tmp_path]
