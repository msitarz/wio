# SPDX-License-Identifier: Apache-2.0
"""Tests for the adapters of `wio.env`."""

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from wio.env import adapters

if TYPE_CHECKING:
    from wio.env.ports import Environment

ROOT = Path(__file__).resolve().parents[3]


def _wired() -> Environment:
    """Wire the adapter where the port is expected.

    Returns:
        A `ProcessEnvironment`, which type checking accepts as an `Environment`.
    """
    return adapters.ProcessEnvironment()


def test_the_module_holds_the_adapters_of_the_ports_that_have_one() -> None:
    """AC-5: only `Environment` has an adapter; the other ports wait for a Work."""
    # Given the module that holds the adapters of wio.env

    # When its public classes are listed
    public = [
        name
        for name, value in vars(adapters).items()
        if isinstance(value, type) and value.__module__ == adapters.__name__
    ]

    # Then the adapter of the environment is the only one
    assert public == ["ProcessEnvironment"]


def test_the_working_directory_is_the_absolute_directory_of_the_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-5: `working_directory()` is where the process runs, as an absolute path."""
    # Given a process running in a directory
    monkeypatch.chdir(tmp_path)

    # When working_directory runs
    directory = _wired().working_directory()

    # Then it is the absolute path of that directory
    assert directory.is_absolute()
    assert directory == tmp_path.resolve()


def test_the_other_members_name_themselves_and_the_work_that_implements_them() -> None:
    """AC-5: `get` raises `NotImplementedError` and says who implements it."""
    # Given a ProcessEnvironment
    environment = _wired()

    # When each member other than working_directory runs
    # Then it raises NotImplementedError naming the member and the Work
    with pytest.raises(NotImplementedError) as caught:
        environment.get("HOME")
    assert str(caught.value) == "get is implemented by the Work that first needs it"


def _bans_cwd(filename: str) -> bool:
    """Say whether ruff bans reading the working directory in a file.

    Args:
        filename: The path to lint a probe as, which picks the per-file ignores.

    Returns:
        Whether ruff reported the ban for `Path.cwd()` and `os.getcwd()`.
    """
    probe = "import os\nfrom pathlib import Path\n\nHERE = (Path.cwd(), os.getcwd())\n"
    ruff = Path(sys.executable).parent / "ruff"
    done = subprocess.run(
        [str(ruff), "check", "--stdin-filename", filename, "-"],
        cwd=ROOT,
        input=probe,
        capture_output=True,
        text=True,
        check=False,
    )
    return done.stdout.count("banned-api") == 2


@pytest.mark.slow
def test_only_the_environment_adapter_may_read_the_working_directory() -> None:
    """AC-5: ruff bans `Path.cwd` and `os.getcwd` outside `wio.env.adapters`."""
    # Given probes that read the working directory, linted as other files

    # When ruff checks each
    reported = {
        name: _bans_cwd(name)
        for name in (
            "src/wio/io/probe.py",
            "src/wio/env/probe.py",
            "src/wio/env/adapters.py",
        )
    }

    # Then only the adapter of the environment is let through
    assert reported == {
        "src/wio/io/probe.py": True,
        "src/wio/env/probe.py": True,
        "src/wio/env/adapters.py": False,
    }
