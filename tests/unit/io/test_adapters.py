# SPDX-License-Identifier: Apache-2.0
"""Tests for the adapters of `wio.io`."""

import io
from typing import TYPE_CHECKING

from wio.io import adapters

if TYPE_CHECKING:
    import pytest


def test_the_module_holds_the_adapters_of_the_ports_that_have_one() -> None:
    """Each port of `wio.io` has one adapter in the module, and no more."""
    # Given the module that holds the adapters

    # When its public classes are listed
    public = sorted(
        name
        for name, value in vars(adapters).items()
        if isinstance(value, type)
        and value.__module__ == adapters.__name__
        and not name.startswith("_")
    )

    # Then the adapters for files, the repository, its history and standard streams
    # are there
    assert public == ["GitHistory", "GitRepository", "LocalFileSystem", "SystemStdio"]


def test_the_standard_streams_adapter_reads_the_streams_when_it_is_created(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The adapter binds the streams at creation, not when the module loads."""
    # Given replacement streams installed after the module was imported
    out, err, source = io.StringIO(), io.StringIO(), io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    monkeypatch.setattr("sys.stderr", err)
    monkeypatch.setattr("sys.stdin", source)

    # When the adapter is created
    stdio = adapters.SystemStdio()

    # Then it hands out the replacements
    assert (stdio.stdin, stdio.stdout, stdio.stderr) == (source, out, err)
