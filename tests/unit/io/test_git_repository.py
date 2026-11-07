# SPDX-License-Identifier: Apache-2.0
"""Tests for `GitRepository`, the adapter of the `Repository` port."""

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.support import enter, git
from tests.unit.env.fakes import FakeEnvironment
from wio.env.adapters import ProcessEnvironment
from wio.io import adapters

if TYPE_CHECKING:
    from tests.sandbox import Sandbox
    from wio.env.ports import Environment
    from wio.io.ports import Repository

STUB = pytest.mark.skip(reason="stub of the architecture stage")


def _wired(environment: Environment | None = None) -> Repository:
    """Wire the adapter where the port is expected.

    Args:
        environment: Where the working directory comes from; the process's own
            by default.

    Returns:
        A `GitRepository`, which type checking accepts as a `Repository`.
    """
    return adapters.GitRepository(environment or ProcessEnvironment())


@pytest.mark.slow
def test_root_and_identity_from_a_subdirectory(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: the root is the top of the tree and the identity its `.git`."""
    # Given a repository with a subdirectory, and the process running in it
    git(sandbox, "init", "-q", check=True)
    sub = sandbox.root / "sub"
    sub.mkdir()
    enter(sandbox, monkeypatch)
    monkeypatch.chdir(sub)

    # When root and identity run
    repository = _wired()
    root, identity = repository.root(), repository.identity()

    # Then they are the absolute top of the tree and its `.git` directory
    assert root == sandbox.root.resolve()
    assert identity == (sandbox.root / ".git").resolve()


@pytest.mark.slow
def test_a_linked_worktree_shares_the_identity_but_not_the_root(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: worktrees of one clone have one identity and different roots."""
    # Given a clone and a linked worktree
    git(sandbox, "init", "-q", check=True)
    git(sandbox, "commit", "-q", "--allow-empty", "-m", "start", check=True)
    linked = sandbox.root.parent / "linked"
    git(sandbox, "worktree", "add", "-q", str(linked), check=True)
    repository = _wired()

    # When identity runs in each
    enter(sandbox, monkeypatch)
    first = (repository.root(), repository.identity())
    monkeypatch.chdir(linked)
    second = (repository.root(), repository.identity())

    # Then both return the same path, and the roots differ
    assert first[1] == second[1]
    assert first[0] != second[0]


@pytest.mark.slow
def test_outside_a_repository_root_and_identity_raise(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: outside a repository both raise `RuntimeError`."""
    # Given a directory that no repository contains
    enter(sandbox, monkeypatch)
    repository = _wired()

    # When root or identity runs
    # Then it raises RuntimeError
    with pytest.raises(RuntimeError):
        repository.root()
    with pytest.raises(RuntimeError):
        repository.identity()


@pytest.mark.slow
def test_the_members_trailers_owns_raise_not_implemented(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-4: show_index and is_dirty name the trailers Work."""
    # Given a GitRepository in a repository
    git(sandbox, "init", "-q", check=True)
    enter(sandbox, monkeypatch)
    repository = _wired()

    # When show_index and is_dirty run
    # Then each raises NotImplementedError naming the trailers Work
    with pytest.raises(NotImplementedError, match="trailers Work"):
        repository.show_index(sandbox.root / "f")
    with pytest.raises(NotImplementedError, match="trailers Work"):
        repository.is_dirty()


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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-3: the adapter asks `rev-parse` for the top and the common directory."""
    # Given a git that answers with a path
    done = subprocess.CompletedProcess([], 0, stdout="/r/.git\n", stderr="")
    calls = _fake_run(monkeypatch, done)

    # When root and identity run
    repository = _wired()
    root, identity = repository.root(), repository.identity()

    # Then both read the printed path and ask the commands the contract names
    assert (root, identity) == (Path("/r/.git"), Path("/r/.git"))
    assert calls == [
        ["git", "rev-parse", "--show-toplevel"],
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
    ]


def test_a_failing_or_missing_git_raises_runtime_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-3: a git that rejects the directory, or is absent, raises."""
    # Given a git that fails, and then one that cannot be started
    _fake_run(monkeypatch, subprocess.CompletedProcess([], 128, "", "fatal: no"))
    repository = _wired()

    # When root runs in each case
    # Then it raises RuntimeError
    with pytest.raises(RuntimeError, match="not inside a git repository"):
        repository.root()

    def missing(*_: object, **__: object) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", missing)
    with pytest.raises(RuntimeError, match="cannot run git"):
        repository.root()


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


@STUB
@pytest.mark.slow
def test_the_root_is_found_from_the_directory_the_environment_reports(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: git runs where the environment says, not where the process is."""
    # Given a repository with a subdirectory, and a process running outside it
    git(sandbox, "init", "-q", check=True)
    sub = sandbox.root / "sub"
    sub.mkdir()
    enter(sandbox, monkeypatch)
    monkeypatch.chdir(sandbox.root.parent)
    repository = _wired(FakeEnvironment(sub))

    # When root runs
    root = repository.root()

    # Then it is the top of that repository
    assert root == sandbox.root.resolve()


@STUB
def test_git_runs_in_the_directory_the_environment_reports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-3: the directory is handed to git as its working directory."""
    # Given a git that records how it is run, and an environment's directory
    seen: list[object] = []
    done = subprocess.CompletedProcess([], 0, stdout="/r\n", stderr="")

    def run(_command: list[str], **options: object) -> subprocess.CompletedProcess[str]:
        seen.append(options.get("cwd"))
        return done

    monkeypatch.setattr(subprocess, "run", run)
    repository = _wired(FakeEnvironment(Path("/somewhere")))

    # When root runs
    repository.root()

    # Then git was run in that directory
    assert seen == [Path("/somewhere")]


@STUB
def test_the_error_names_the_directory_the_environment_reports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-3: outside a repository the message names the environment's directory."""
    # Given a git that rejects the directory
    _fake_run(monkeypatch, subprocess.CompletedProcess([], 128, "", "fatal: no"))
    repository = _wired(FakeEnvironment(Path("/somewhere")))

    # When root runs
    with pytest.raises(RuntimeError) as caught:
        repository.root()

    # Then the message names that directory
    assert "/somewhere" in str(caught.value)
