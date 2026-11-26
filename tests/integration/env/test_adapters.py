# SPDX-License-Identifier: Apache-2.0
"""Tests of the adapters of `wio.env` against the real process."""

import time
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.sandbox import unreadable
from wio.env import adapters

if TYPE_CHECKING:
    from collections.abc import Iterator

    from wio.env.ports import Clock, Directories, Environment


def _wired() -> Environment:
    """Wire the adapter where the port is expected.

    Returns:
        A `ProcessEnvironment`, which type checking accepts as an `Environment`.
    """
    return adapters.ProcessEnvironment()


def _wired_clock() -> Clock:
    """Wire the clock adapter where the port is expected.

    Returns:
        A `SystemClock`, which type checking accepts as a `Clock`.
    """
    return adapters.SystemClock()


def _wired_directories() -> Directories:
    """Wire the directories adapter where the port is expected.

    Returns:
        A `ProcessDirectories`, which type checking accepts as `Directories`.
    """
    return adapters.ProcessDirectories(adapters.ProcessEnvironment())


def test_the_adapters_are_wired_where_their_ports_are_expected() -> None:
    """C-1: the adapters satisfy the ports that the other Works read them through."""
    # Given the adapters wired where the ports are expected
    # When they are built
    clock, directories = _wired_clock(), _wired_directories()

    # Then they are the adapters of the module
    assert isinstance(clock, adapters.SystemClock)
    assert isinstance(directories, adapters.ProcessDirectories)


def test_the_working_directory_is_the_absolute_directory_of_the_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`working_directory()` is where the process runs, as an absolute path."""
    # Given a process running in a directory
    monkeypatch.chdir(tmp_path)

    # When the working directory is asked for
    directory = _wired().working_directory()

    # Then it is the absolute path of that directory
    assert directory.is_absolute()
    assert directory == tmp_path.resolve()


def _home_failing(*, relative: bool) -> Path:
    """Stand in for `Path.home()` that cannot find a usable home.

    Args:
        relative: Whether to return a relative path instead of raising.

    Returns:
        `Path("rel")` when `relative` is true.

    Raises:
        RuntimeError: When `relative` is false, as `Path.home()` does.
    """
    if relative:
        return Path("rel")
    message = "no home"
    raise RuntimeError(message)


def test_a_variable_is_read_as_it_is_at_the_time_of_the_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-1: set, unset and empty values, and a value that changes between reads."""
    # Given a process with a set, an unset and an empty variable
    monkeypatch.setenv("WIO_TEST_VALUE", "abc")
    monkeypatch.delenv("WIO_TEST_UNSET", raising=False)
    monkeypatch.setenv("WIO_TEST_EMPTY", "")
    environment = adapters.ProcessEnvironment()

    # When each is read, the set one is changed, and it is read again
    values = [environment.get(n) for n in ("WIO_TEST_VALUE", "WIO_TEST_UNSET")]
    empty = environment.get("WIO_TEST_EMPTY")
    monkeypatch.setenv("WIO_TEST_VALUE", "def")
    again = environment.get("WIO_TEST_VALUE")

    # Then they give the value, None, an empty string, and the new value
    assert (values, empty, again) == (["abc", None], "", "def")


def test_the_clock_gives_seconds_since_the_epoch() -> None:
    """AC-2: a reading lies between the system's times around the call."""
    # Given the times that time.time() gives around the call
    before = time.time()

    # When the clock is read
    reading = adapters.SystemClock().now()
    after = time.time()

    # Then it is a float between them
    assert isinstance(reading, float)
    assert before <= reading <= after


def test_the_wio_home_is_the_one_that_the_process_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: `$WIO_HOME` is given as it is, without being created or tested."""
    # Given $WIO_HOME naming a path that does not exist
    home = tmp_path / "wio-home-test"
    monkeypatch.setenv("WIO_HOME", str(home))
    directories = adapters.ProcessDirectories(adapters.ProcessEnvironment())

    # When the Wio home is asked for
    found = directories.wio_home()

    # Then it is that path, and it still does not exist
    assert found == home
    assert not home.exists()


def test_a_wio_home_that_cannot_be_written_is_given_as_it_is(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: a home under a regular file raises nothing."""
    # Given $WIO_HOME naming a path under a regular file
    blocker = tmp_path / "file"
    blocker.write_text("x", encoding="utf-8")
    home = blocker / "wio"
    monkeypatch.setenv("WIO_HOME", str(home))
    directories = adapters.ProcessDirectories(adapters.ProcessEnvironment())

    # When the Wio home is asked for
    found = directories.wio_home()

    # Then it is that path
    assert found == home


@pytest.mark.parametrize("value", [None, ""])
def test_the_default_wio_home_is_under_the_home_of_the_user(
    value: str | None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: an unset or empty `$WIO_HOME` gives `.agents/wio` under the user home."""
    # Given $WIO_HOME unset or empty and a user home that does not exist
    user_home = tmp_path / "user-home-test"
    monkeypatch.setattr(Path, "home", lambda: user_home)
    if value is None:
        monkeypatch.delenv("WIO_HOME", raising=False)
    else:
        monkeypatch.setenv("WIO_HOME", value)
    directories = adapters.ProcessDirectories(adapters.ProcessEnvironment())

    # When the Wio home is asked for
    found = directories.wio_home()

    # Then it is .agents/wio under it, and the user home was not created
    assert found == user_home / ".agents" / "wio"
    assert not user_home.exists()


def test_the_home_of_the_user_is_read_only_when_it_is_needed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: a named home never asks `Path.home()`, which here would raise."""
    # Given $WIO_HOME set and a Path.home() that raises RuntimeError
    home = tmp_path / "wio-home-test"
    monkeypatch.setenv("WIO_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: _home_failing(relative=False))
    directories = adapters.ProcessDirectories(adapters.ProcessEnvironment())

    # When the Wio home is asked for
    found = directories.wio_home()

    # Then it is the named path
    assert found == home


@pytest.mark.parametrize("relative", [False, True])
def test_a_user_home_that_is_missing_or_relative_is_an_oserror(
    monkeypatch: pytest.MonkeyPatch, *, relative: bool
) -> None:
    """AC-3: a `Path.home()` that raises or gives a relative path is an `OSError`."""
    # Given $WIO_HOME unset and a Path.home() that raises or is relative
    monkeypatch.delenv("WIO_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: _home_failing(relative=relative))
    directories = adapters.ProcessDirectories(adapters.ProcessEnvironment())

    # When the Wio home is asked for
    # Then it raises an OSError
    with pytest.raises(OSError, match="home"):
        directories.wio_home()


def test_the_named_temporary_directory_is_returned_without_testing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-empty TMPDIR is returned as given, even when it is relative."""
    # Given a relative temporary directory that need not exist
    monkeypatch.setenv("TMPDIR", "relative/temp")
    directories = adapters.ProcessDirectories(adapters.ProcessEnvironment())

    # When the temporary directory is requested
    found = directories.temp_dir()

    # Then the named path is returned unchanged
    assert found == Path("relative/temp")


@pytest.mark.parametrize("platform", ["darwin", "linux"])
@pytest.mark.parametrize("value", [None, "", "/tmp/t"])
def test_temporary_directory_uses_the_platform_default(
    platform: str, value: str | None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-4: empty and unset TMPDIR use the tested platform directory."""
    # Given two scratch system directories and an environment value
    darwin = tmp_path / "darwin"
    other = tmp_path / "other"
    darwin.mkdir()
    other.mkdir()
    if value is None:
        monkeypatch.delenv("TMPDIR", raising=False)
    else:
        monkeypatch.setenv("TMPDIR", value)
    directories = adapters.ProcessDirectories(
        adapters.ProcessEnvironment(), platform, darwin, other
    )

    # When the temporary directory is requested
    found = directories.temp_dir()

    # Then the named directory or the tested platform default is returned
    expected = Path(value) if value else (darwin if platform == "darwin" else other)
    assert found == expected
    assert list(darwin.iterdir()) == []
    assert list(other.iterdir()) == []


@pytest.mark.parametrize("platform", ["darwin", "linux"])
@pytest.mark.parametrize("kind", ["missing", "file"])
def test_an_unusable_system_temporary_directory_raises(
    platform: str, kind: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The system directory is tested, but an explicit TMPDIR is not."""
    # Given a system directory that is missing or is a regular file
    target = tmp_path / "unusable"
    if kind == "file":
        target.write_text("file", encoding="utf-8")
    monkeypatch.delenv("TMPDIR", raising=False)
    directories = adapters.ProcessDirectories(
        adapters.ProcessEnvironment(), platform, target, target
    )

    # When the system directory is requested
    # Then it fails instead of returning an unusable path
    with pytest.raises(OSError):  # noqa: PT011 - the port promises any OSError
        directories.temp_dir()


def test_an_unwritable_system_directory_is_not_usable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An existing system directory is unusable if a probe cannot be created."""
    # Given an existing system directory that cannot be written
    directory = tmp_path / "closed"
    directory.mkdir()
    monkeypatch.delenv("TMPDIR", raising=False)
    directories = adapters.ProcessDirectories(
        adapters.ProcessEnvironment(), "linux", directory, directory
    )

    # When it is chosen as the default temporary directory
    # Then the failed probe raises an OSError
    with unreadable(directory), pytest.raises(OSError):  # noqa: PT011 - port contract
        directories.temp_dir()


def test_temporary_probe_removal_failure_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Failure to remove the temporary probe makes the directory unusable."""
    # Given an unset TMPDIR and a probe that fails while it is removed
    monkeypatch.delenv("TMPDIR", raising=False)

    @contextmanager
    def failing_probe(**_kwargs: object) -> Iterator[None]:
        """Simulate a successful probe creation and failed removal.

        Yields:
            Control as the open probe.

        Raises:
            OSError: When the probe is removed.
        """
        yield
        message = "probe removal failed"
        raise OSError(message)

    monkeypatch.setattr(adapters.tempfile, "NamedTemporaryFile", failing_probe)
    directories = adapters.ProcessDirectories(
        adapters.ProcessEnvironment(), "linux", tmp_path, tmp_path
    )

    # When the platform temporary directory is requested
    # Then the removal failure propagates as an OSError
    with pytest.raises(OSError, match="probe removal failed"):
        directories.temp_dir()
