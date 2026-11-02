# SPDX-License-Identifier: Apache-2.0
"""Tests for the composition root of the `wio` command."""

import io
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

import pytest

from wio import cli

BEFORE_WIRING = pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason="the wiring stage implements main",
)
BEFORE_IMPLEMENTATION = pytest.mark.xfail(
    strict=True,
    raises=NotImplementedError,
    reason="the wiring stage composes console_main, and the implementation "
    "stage adds the adapter it needs",
)


@dataclass
class FakeStdio:
    """In-memory standard streams that satisfy the `Stdio` port."""

    stdin: TextIO
    stdout: TextIO
    stderr: TextIO


@BEFORE_WIRING
def test_main_returns_zero_and_writes_nothing() -> None:
    """With no arguments the entry point succeeds silently, for now."""
    # Given in-memory streams in place of the standard streams
    out, err = io.StringIO(), io.StringIO()
    stdio = FakeStdio(io.StringIO(), out, err)

    # When the testable core runs with no arguments
    code = cli.main([], stdio)

    # Then it returns 0 and the streams hold nothing
    assert code == 0
    assert (out.getvalue(), err.getvalue()) == ("", "")


@BEFORE_IMPLEMENTATION
def test_console_main_builds_the_real_streams_and_returns_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The console function runs the core on the process's own streams."""
    # Given the process arguments of a bare `wio`
    monkeypatch.setattr("sys.argv", ["wio"])

    # When the console function runs
    code = cli.console_main()

    # Then it returns 0 and prints nothing
    captured = capsys.readouterr()
    assert code == 0
    assert (captured.out, captured.err) == ("", "")


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="the wiring stage removes hello, its module and its test",
)
def test_the_placeholder_is_gone() -> None:
    """Neither the greeting nor its test is left."""
    # Given the package and the unit tests as they are

    # When the placeholder is looked for
    has_greeting = hasattr(cli, "hello")
    has_test = (Path(__file__).parents[1] / "test_cli.py").exists()

    # Then neither exists
    assert (has_greeting, has_test) == (False, False)
