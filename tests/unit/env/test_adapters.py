# SPDX-License-Identifier: Apache-2.0
"""Tests for the adapters of `wio.env`."""

from typing import TYPE_CHECKING

import pytest

from wio.env import adapters

if TYPE_CHECKING:
    from pathlib import Path

    from wio.env.ports import Environment

STUB = pytest.mark.skip(reason="stub of the architecture stage")


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


@STUB
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
