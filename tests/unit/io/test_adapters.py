# SPDX-License-Identifier: Apache-2.0
"""Tests for the adapters of `wio.io`."""

import sys

import pytest

from wio.io import adapters


@pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason="the implementation stage binds the streams of sys",
)
def test_the_standard_streams_adapter_wraps_the_real_streams() -> None:
    """The adapter for standard streams hands out `sys`'s own streams."""
    # Given the adapter for standard streams

    # When it is created
    stdio = adapters.SystemStdio()

    # Then its streams are the process's streams
    assert stdio.stdin is sys.stdin
    assert stdio.stdout is sys.stdout
    assert stdio.stderr is sys.stderr


def test_the_standard_streams_adapter_is_the_only_adapter() -> None:
    """The ports for files and git have no adapter yet."""
    # Given the module that holds the adapters

    # When its public classes are listed
    public = sorted(
        name
        for name, value in vars(adapters).items()
        if isinstance(value, type) and value.__module__ == adapters.__name__
    )

    # Then only the adapter for standard streams is there
    assert public == ["SystemStdio"]
