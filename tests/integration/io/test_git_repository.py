# SPDX-License-Identifier: Apache-2.0
"""Tests for `GitRepository` with real git and real directories behind it."""

import os
from typing import TYPE_CHECKING

import pytest

from tests.support import FakeEnvironment, enter, git
from wio.env.adapters import ProcessEnvironment
from wio.io import adapters

if TYPE_CHECKING:
    from pathlib import Path

    from tests.sandbox import Sandbox
    from wio.env.ports import Environment
    from wio.io.ports import Repository


def _wired(environment: Environment) -> Repository:
    """Wire the adapter where the port is expected.

    Args:
        environment: Where the working directory comes from.

    Returns:
        A `GitRepository`, which type checking accepts as a `Repository`.
    """
    return adapters.GitRepository(environment)


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
    repository = _wired(ProcessEnvironment())
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
    repository = _wired(ProcessEnvironment())

    # When identity runs in each
    enter(sandbox, monkeypatch)
    first = (repository.root(), repository.identity())
    monkeypatch.chdir(linked)
    second = (repository.root(), repository.identity())

    # Then both return the same path, and the roots differ
    assert first[1] == second[1]
    assert first[0] != second[0]


def test_a_working_directory_that_does_not_exist_says_so(tmp_path: Path) -> None:
    """AC-3: a missing directory is named and is not blamed on git."""
    # Given an environment whose directory does not exist
    missing = tmp_path / "gone"
    repository = _wired(FakeEnvironment(missing))

    # When root and identity run
    with pytest.raises(RuntimeError) as root_error:
        repository.root()
    with pytest.raises(RuntimeError) as identity_error:
        repository.identity()

    # Then both name the directory, say it does not exist and say what to do
    for caught in (root_error, identity_error):
        message = str(caught.value)
        assert str(missing) in message
        assert "does not exist" in message
        assert "run wio from a directory inside the repository" in message
        assert "cannot run git" not in message


@pytest.mark.skipif(os.geteuid() == 0, reason="root can enter any directory")
def test_a_working_directory_that_cannot_be_entered_says_so(tmp_path: Path) -> None:
    """AC-3: a directory without permission is named and git is not blamed."""
    # Given an environment whose directory exists but cannot be entered
    locked = tmp_path / "locked"
    locked.mkdir()
    locked.chmod(0o000)
    repository = _wired(FakeEnvironment(locked))

    # When root runs
    try:
        with pytest.raises(RuntimeError) as caught:
            repository.root()
    finally:
        locked.chmod(0o700)

    # Then the message names the directory, says it cannot be entered and what to do
    message = str(caught.value)
    assert str(locked) in message
    assert "cannot be entered" in message
    assert "run wio from a directory inside the repository" in message
    assert "cannot run git" not in message


def test_a_working_directory_that_is_a_file_says_so(tmp_path: Path) -> None:
    """AC-3: a directory that is a file is named and is not blamed on git."""
    # Given an environment whose directory is a file
    file = tmp_path / "file"
    file.write_text("x", encoding="utf-8")
    repository = _wired(FakeEnvironment(file))

    # When root runs
    with pytest.raises(RuntimeError) as caught:
        repository.root()

    # Then the message names the file, says it is not a directory and what to do
    message = str(caught.value)
    assert str(file) in message
    assert "is not a directory" in message
    assert "run wio from a directory inside the repository" in message


@pytest.mark.slow
def test_a_real_directory_outside_a_repository_says_so(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: with a real git, root and identity name the directory and the next step."""
    # Given a directory that no repository contains, and a real git
    enter(sandbox, monkeypatch)
    repository = _wired(FakeEnvironment(sandbox.root))

    # When root and identity run
    with pytest.raises(RuntimeError) as root_error:
        repository.root()
    with pytest.raises(RuntimeError) as identity_error:
        repository.identity()

    # Then each message names that directory and says what to do
    for caught in (root_error, identity_error):
        message = str(caught.value)
        assert str(sandbox.root) in message
        assert "not inside a git repository" in message
        assert "inside the repository" in message


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
