# SPDX-License-Identifier: Apache-2.0
"""Tests for `wio.log.locate` against real git and a real disk."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.support import enter, git
from wio.env.adapters import ProcessDirectories, ProcessEnvironment
from wio.io.adapters import GitRepository, LocalFileSystem
from wio.log.locate import locate_log, log_files

if TYPE_CHECKING:
    from tests.sandbox import Sandbox


def _locate() -> Path:
    """Find the log of the repository the process runs in, with the real ports.

    Returns:
        What `locate_log` gives for git and the real directories.
    """
    environment = ProcessEnvironment()
    return locate_log(GitRepository(environment), ProcessDirectories(environment))


def _home(sandbox: Sandbox) -> Path:
    """Create the empty directory that `$WIO_HOME` names in the sandbox.

    Args:
        sandbox: The sandbox whose `WIO_HOME` is used.

    Returns:
        The empty directory.
    """
    home = Path(sandbox.env["WIO_HOME"])
    home.mkdir()
    return home


@pytest.mark.slow
def test_worktrees_of_one_clone_share_a_location(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-1: the main checkout and a worktree of it find the same log."""
    # Given a real clone with a commit, a worktree of it and an empty $WIO_HOME
    git(sandbox, "init", "-q", check=True)
    git(sandbox, "commit", "-q", "--allow-empty", "-m", "start", check=True)
    linked = sandbox.root.parent / "linked"
    git(sandbox, "worktree", "add", "-q", str(linked), check=True)
    _home(sandbox)
    enter(sandbox, monkeypatch)

    # When locate_log runs from the main checkout and from the worktree
    from_main = _locate()
    monkeypatch.chdir(linked)
    from_worktree = _locate()

    # Then both give the same path
    assert from_main == from_worktree


@pytest.mark.slow
def test_finding_the_location_creates_nothing(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-4: $WIO_HOME still holds nothing."""
    # Given a real clone and a $WIO_HOME that names an empty directory
    git(sandbox, "init", "-q", check=True)
    home = _home(sandbox)
    enter(sandbox, monkeypatch)

    # When locate_log runs
    found = _locate()

    # Then it gives a path under $WIO_HOME/log/ and $WIO_HOME holds nothing
    assert found.parent == home / "log"
    assert list(home.iterdir()) == []


@pytest.mark.slow
def test_outside_a_repository_the_error_of_the_port_is_raised(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-4: the `RuntimeError` of git reaches the caller unchanged."""
    # Given a working directory that is not in a repository
    enter(sandbox, monkeypatch)

    # When locate_log runs with the Repository of git
    # Then the RuntimeError of the port is raised unchanged
    with pytest.raises(RuntimeError, match="repository"):
        _locate()


@pytest.mark.slow
def test_a_relative_wio_home_raises_the_error_of_the_port(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-4: the `ValueError` of the directories reaches the caller unchanged."""
    # Given a real clone and $WIO_HOME set to relative/dir
    git(sandbox, "init", "-q", check=True)
    enter(sandbox, monkeypatch)
    monkeypatch.setenv("WIO_HOME", "relative/dir")

    # When locate_log runs with the real Directories
    # Then the ValueError of the port is raised unchanged
    with pytest.raises(ValueError, match="relative"):
        _locate()


def test_a_symlink_to_a_file_is_found_and_one_to_a_directory_is_not(
    tmp_path: Path,
) -> None:
    """AC-3: the real `is_file` follows a symlink to a file and not to a directory."""
    # Given a directory on disk that holds link.jsonl, a symlink to a file, and
    # dir.jsonl, a symlink to a directory
    target = tmp_path / "target.txt"
    target.write_text("{}\n", encoding="utf-8")
    other = tmp_path / "other"
    other.mkdir()
    log = tmp_path / "log"
    log.mkdir()
    (log / "link.jsonl").symlink_to(target)
    (log / "dir.jsonl").symlink_to(other, target_is_directory=True)

    # When log_files runs for it with the real FileSystem
    found = log_files(log, LocalFileSystem())

    # Then it gives link.jsonl and not dir.jsonl
    assert found == (log / "link.jsonl",)


def test_a_missing_directory_stays_missing(tmp_path: Path) -> None:
    """AC-3: looking for the files of a log creates nothing."""
    # Given a path on disk that does not exist
    missing = tmp_path / "log"

    # When log_files runs for it with the real FileSystem
    found = log_files(missing, LocalFileSystem())

    # Then it gives no file and the path still does not exist
    assert found == ()
    assert not missing.exists()
