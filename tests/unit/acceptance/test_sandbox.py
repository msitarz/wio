# SPDX-License-Identifier: Apache-2.0
"""Tests for the sandbox of the acceptance test drivers."""

from pathlib import Path

import pytest

from tests.acceptance.sandbox import Sandbox
from tests.support import git


def test_the_sandbox_lies_inside_the_temporary_directory(tmp_path: Path) -> None:
    """The root and `WIO_HOME` are under the test's own directory."""
    # Given a temporary directory of a test

    # When a sandbox is made from it and its root and environment are read
    sandbox = Sandbox.under(tmp_path)

    # Then the root is a directory under it, and so is the Wio home
    assert sandbox.root.is_dir()
    assert sandbox.root.is_relative_to(tmp_path)
    assert Path(sandbox.env["WIO_HOME"]).is_relative_to(tmp_path)


def test_the_sandbox_keeps_the_rest_of_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`PATH` and `HOME` are not dropped or replaced."""
    # Given a temporary directory of a test and a home directory in the process
    monkeypatch.setenv("HOME", "/the/developers/home")

    # When a sandbox is made from it
    sandbox = Sandbox.under(tmp_path)

    # Then it carries the process's PATH and HOME
    assert "PATH" in sandbox.env
    assert sandbox.env["HOME"] == "/the/developers/home"


def test_the_sandbox_replaces_what_git_and_wio_would_take_from_outside(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The Wio home, git config, the ceiling and the identity are the sandbox's."""
    # Given a process that has its own Wio home and a git identity
    monkeypatch.setenv("WIO_HOME", "/the/developers/wio")
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Someone Else")

    # When a sandbox is made from a temporary directory
    sandbox = Sandbox.under(tmp_path)

    # Then none of it shows, and git is told to read nothing from outside
    env = sandbox.env
    assert env["WIO_HOME"] == str(tmp_path / "wio-home")
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert Path(env["GIT_CONFIG_GLOBAL"]).is_relative_to(tmp_path)
    assert env["GIT_CEILING_DIRECTORIES"] == str(tmp_path.resolve())
    assert env["GIT_AUTHOR_NAME"] == env["GIT_COMMITTER_NAME"] == "Wio Test"
    assert env["GIT_AUTHOR_DATE"] == env["GIT_COMMITTER_DATE"]


def test_the_sandbox_drops_the_variables_that_aim_git_elsewhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Variables a git hook sets, and git's tracing, are not passed on."""
    # Given a process that runs under a git hook with tracing on
    for name in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_TRACE"):
        monkeypatch.setenv(name, "/elsewhere")

    # When a sandbox is made from a temporary directory
    sandbox = Sandbox.under(tmp_path)

    # Then none of them is in its environment
    for name in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_TRACE"):
        assert name not in sandbox.env


@pytest.mark.slow
def test_git_in_the_sandbox_reads_nothing_from_the_developer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Global config, a repository above and a redirect have no effect."""
    # Given a home with a global git config and ignore file, a repository
    # that contains the temporary directory, and a git hook's GIT_DIR
    home = tmp_path / "home"
    (home / ".config" / "git").mkdir(parents=True)
    (home / ".gitconfig").write_text("[user]\n\tname = Leak\n", encoding="utf-8")
    (home / ".config" / "git" / "ignore").write_text("*\n", encoding="utf-8")
    outer = tmp_path / "outer"
    inner = outer / "inner"
    inner.mkdir(parents=True)
    setup = Sandbox.under(tmp_path / "setup")
    git(setup, "init", "-q", str(outer), check=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("GIT_DIR", str(outer / ".git"))
    sandbox = Sandbox.under(inner)

    # When git runs in the sandbox
    name = git(sandbox, "config", "user.name")
    toplevel = git(sandbox, "rev-parse", "--show-toplevel")
    git(sandbox, "init", "-q")
    (sandbox.root / "a.txt").write_text("a", encoding="utf-8")
    status = git(sandbox, "status", "--porcelain")

    # Then it has no global config, no repository above, and no global ignore
    assert name.returncode == 1
    assert toplevel.returncode != 0
    assert status.stdout.strip() == "?? a.txt"
