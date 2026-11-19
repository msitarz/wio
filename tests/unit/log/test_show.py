# SPDX-License-Identifier: Apache-2.0
"""Check read failures at the report's port boundary.

A fake filesystem can make a file fail immediately after it was discovered.
"""

from pathlib import Path

import pytest

from tests.unit.fakes import FakeDirectories, FakeRepository, MemoryFileSystem
from wio.log.errors import LogError
from wio.log.show import read_report


@pytest.mark.parametrize(
    "error",
    [FileNotFoundError("the listed file vanished"), PermissionError("read denied")],
)
def test_listed_log_file_read_errors_fail_the_report(error: OSError) -> None:
    """AC-4 reports an unreadable listed file as a failure.

    Args:
        error: The failure to inject when reading the listed event file.
    """
    # Given a file that is present when listed but fails on read.
    repository = FakeRepository(top=Path("/w/app"))
    directories = FakeDirectories(Path("/h"))
    path = Path("/h/log/app-6f8609bd196b/events.jsonl")
    filesystem = MemoryFileSystem(files={path: ""}, broken={path: error})

    # When the report reads it.
    with pytest.raises(LogError) as raised:
        read_report(repository, directories, filesystem)

    # Then the original error remains available with its message.
    assert str(raised.value) == str(error)
    assert raised.value.__cause__ is error


def test_invalid_wio_home_fails_before_reading() -> None:
    """AC-4 preserves a location error raised by Directories.

    The file port remains untouched when the location cannot be determined.
    """
    # Given a Wio home lookup that reports an invalid setting.
    repository = FakeRepository()
    error = ValueError("WIO_HOME must be absolute")
    directories = FakeDirectories(error)
    filesystem = MemoryFileSystem()

    # When the report is read.
    with pytest.raises(LogError) as raised:
        read_report(repository, directories, filesystem)

    # Then the original failure is reported before any filesystem calls.
    assert raised.value.__cause__ is error
    assert not filesystem.calls
