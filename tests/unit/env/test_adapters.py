# SPDX-License-Identifier: Apache-2.0
"""Tests for the adapters of `wio.env`."""

from pathlib import Path

import pytest

from tests.fakes import FakeEnvironment
from wio.env import adapters


def test_the_module_holds_the_adapters_of_the_ports() -> None:
    """The adapters of the environment, the clock, the directories and randomness."""
    # Given the module that holds the adapters of the environment component

    # When its public classes are listed
    public = [
        name
        for name, value in vars(adapters).items()
        if isinstance(value, type) and value.__module__ == adapters.__name__
    ]

    # Then the adapters of the four ports are the only ones
    assert sorted(public) == [
        "ProcessDirectories",
        "ProcessEnvironment",
        "SystemClock",
        "SystemEntropy",
    ]


def test_the_named_temporary_directory_is_given_without_a_probe() -> None:
    """A non-empty TMPDIR is returned without checking its existence."""
    # Given an environment naming a temporary path
    environment = FakeEnvironment(Path(), {"TMPDIR": "relative/missing"})
    directories = adapters.ProcessDirectories(environment)

    # When the temporary directory is asked for
    found = directories.temp_dir()

    # Then the named path is returned and the variable is read once
    assert found == Path("relative/missing")
    assert environment.reads == ["TMPDIR"]


def test_the_entropy_gives_exactly_the_bytes_asked_for() -> None:
    """The adapter reads as many bytes as it is asked for, and differs between calls."""
    # Given the adapter of randomness
    entropy = adapters.SystemEntropy()

    # When it is asked for six bytes, twice, and for none
    first, second, none = entropy.random_bytes(6), entropy.random_bytes(6), b""

    # Then each is six bytes long, the two differ, and none is empty
    assert (len(first), len(second)) == (6, 6)
    assert first != second
    assert entropy.random_bytes(0) == none


def test_the_wio_home_is_read_from_the_environment_it_is_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: a fake `Environment` decides the home, and the home is not created."""
    # Given a process with another WIO_HOME, and a ProcessDirectories built with
    # a fake whose WIO_HOME is fake-home
    monkeypatch.setenv("WIO_HOME", str(tmp_path / "process-home"))
    home = tmp_path / "fake-home"
    directories = adapters.ProcessDirectories(
        FakeEnvironment(tmp_path, {"WIO_HOME": str(home)})
    )

    # When the Wio home is asked for
    found = directories.wio_home()

    # Then it is the path of the fake, and nothing was created
    assert found == home
    assert not home.exists()


def test_the_wio_home_follows_the_environment_at_each_call(tmp_path: Path) -> None:
    """AC-3: one `ProcessDirectories` gives `a` and then `b` as the fake changes."""
    # Given one ProcessDirectories whose fake Environment names a
    fake = FakeEnvironment(tmp_path, {"WIO_HOME": str(tmp_path / "a")})
    directories = adapters.ProcessDirectories(fake)

    # When it runs, the fake is changed to name b, and it runs again
    first = directories.wio_home()
    fake.variables["WIO_HOME"] = str(tmp_path / "b")
    second = directories.wio_home()

    # Then the first gives a and the second b
    assert (first, second) == (tmp_path / "a", tmp_path / "b")


def test_a_relative_wio_home_is_refused_by_name(tmp_path: Path) -> None:
    """AC-3: a relative `WIO_HOME` raises a `ValueError` naming it and `absolute`."""
    # Given a ProcessDirectories whose WIO_HOME is relative
    directories = adapters.ProcessDirectories(
        FakeEnvironment(tmp_path, {"WIO_HOME": "relative/dir"})
    )

    # When the Wio home is asked for
    # Then it raises a ValueError that names WIO_HOME and holds absolute
    with pytest.raises(ValueError, match=r"WIO_HOME.*absolute"):
        directories.wio_home()
