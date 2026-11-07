# SPDX-License-Identifier: Apache-2.0
"""Tests for the sandbox of the acceptance test drivers."""

from pathlib import Path
from typing import TYPE_CHECKING

from tests.sandbox import Sandbox

if TYPE_CHECKING:
    import pytest


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
