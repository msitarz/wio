# SPDX-License-Identifier: Apache-2.0
"""Helpers that tests share: running git in a sandbox, and a fake `Environment`."""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

    from tests.sandbox import Sandbox


_ROOT = Path(__file__).resolve().parents[1]

_IMPORT_LIGHT = """
import argparse, importlib, json, sys
name = sys.argv[1]
importlib.import_module(name).describe().configure(argparse.ArgumentParser())
sys.stdout.write(json.dumps(sorted(m for m in sys.modules if m.startswith(name + "."))))
"""


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


def import_light_violations(module: str) -> list[str]:
    """List the modules a command's package loads only to be described.

    In a fresh interpreter it imports the package, calls its `describe()` and
    the `configure` of the spec that returns, and lists what it loaded.

    Args:
        module: The dotted name of the package whose `describe` it calls.

    Returns:
        The sorted names of the modules under the package, other than its
        `__init__`, that are loaded by then. An empty list means it is light.
    """
    done = subprocess.run(
        [sys.executable, "-c", _IMPORT_LIGHT, module],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    names: list[str] = json.loads(done.stdout)
    return names


@dataclass
class FakeEnvironment:
    """An `Environment` with a fixed working directory and the given variables."""

    directory: Path
    variables: dict[str, str] = field(default_factory=dict)

    def get(self, name: str) -> str | None:
        """Read a variable of the fake.

        Args:
            name: The variable's name.

        Returns:
            Its value, or None when the fake has no such variable.
        """
        return self.variables.get(name)

    def working_directory(self) -> Path:
        """Find the fixed working directory.

        Returns:
            The directory the fake was given.
        """
        return self.directory
