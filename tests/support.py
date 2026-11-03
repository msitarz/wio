# SPDX-License-Identifier: Apache-2.0
"""Helpers that tests share, such as running git in a sandbox."""

import os
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

    from tests.sandbox import Sandbox


def git(
    sandbox: Sandbox, *args: str, check: bool = False
) -> subprocess.CompletedProcess[str]:
    """Run git in the sandbox's directory and environment.

    Args:
        sandbox: Where to run it.
        *args: The arguments after `git`.
        check: Whether a non-zero exit code raises.

    Returns:
        The completed process, with its output decoded.
    """
    return subprocess.run(
        ["git", *args],
        cwd=sandbox.root,
        env=sandbox.env,
        capture_output=True,
        text=True,
        check=check,
    )


def enter(sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the sandbox's directory and environment the process's own.

    For code under test that runs git itself, without an environment argument.
    The test's monkeypatch puts everything back afterwards.

    Args:
        sandbox: The sandbox to enter.
        monkeypatch: The test's monkeypatch fixture.
    """
    for name in set(os.environ) - set(sandbox.env):
        monkeypatch.delenv(name)
    for name, value in sandbox.env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(sandbox.root)
