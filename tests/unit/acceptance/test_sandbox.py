# SPDX-License-Identifier: Apache-2.0
"""Tests for the sandbox of the acceptance test drivers."""

from pathlib import Path

from tests.acceptance.sandbox import Sandbox


def test_the_sandbox_lies_inside_the_temporary_directory(tmp_path: Path) -> None:
    """The root, `HOME` and `XDG_DATA_HOME` are under the test's own directory."""
    # Given a temporary directory of a test

    # When a sandbox is made from it and its root and environment are read
    sandbox = Sandbox.under(tmp_path)

    # Then the root is a directory under it, and so are the two variables
    assert sandbox.root.is_dir()
    assert sandbox.root.is_relative_to(tmp_path)
    assert Path(sandbox.env["HOME"]).is_relative_to(tmp_path)
    assert Path(sandbox.env["XDG_DATA_HOME"]).is_relative_to(tmp_path)


def test_the_sandbox_keeps_the_rest_of_the_environment(tmp_path: Path) -> None:
    """The command can still be found, because `PATH` is not dropped."""
    # Given a temporary directory of a test

    # When a sandbox is made from it
    sandbox = Sandbox.under(tmp_path)

    # Then it carries the process's PATH
    assert "PATH" in sandbox.env
