# SPDX-License-Identifier: Apache-2.0
"""Tests of the adapters of `wio.env` against the real process."""

from typing import TYPE_CHECKING

from wio.env import adapters

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from wio.env.ports import Environment


def _wired() -> Environment:
    """Wire the adapter where the port is expected.

    Returns:
        A `ProcessEnvironment`, which type checking accepts as an `Environment`.
    """
    return adapters.ProcessEnvironment()


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
