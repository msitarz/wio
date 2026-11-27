# SPDX-License-Identifier: Apache-2.0
"""Unit tests for `wio.describe.command`."""

import argparse
import io
import json
from dataclasses import dataclass
from typing import TextIO

import pytest

from wio.describe import DescribeCommand, describe
from wio.errors import WioError


@dataclass
class _FakeStdio:
    """Minimal in-memory `Stdio` for unit testing `DescribeCommand`."""

    stdin: TextIO
    stdout: TextIO
    stderr: TextIO


def _stdio() -> tuple[_FakeStdio, io.StringIO]:
    """Build a fresh in-memory `Stdio` and its captured stdout buffer."""
    out = io.StringIO()
    return _FakeStdio(io.StringIO(), out, io.StringIO()), out


def _parse(argv: list[str]) -> argparse.Namespace:
    """Parse `argv` through `DescribeSpec`."""
    parser = argparse.ArgumentParser(prog="wio describe")
    describe().configure(parser)
    return parser.parse_args(argv)


def test_describe_command_runs_engine_overview_text_and_json() -> None:
    """`DescribeCommand` writes engine overview text or JSON and returns 0."""
    # Given parsed arguments for bare `describe` and `describe --json`
    text_io, text_out = _stdio()
    json_io, json_out = _stdio()
    cmd = DescribeCommand()

    # When run for text and JSON
    text_code = cmd.run(_parse([]), text_io)
    json_code = cmd.run(_parse(["--json"]), json_io)

    # Then both succeed and write valid output
    assert text_code == 0
    assert json_code == 0
    assert "Commands:" in text_out.getvalue()
    assert json.loads(json_out.getvalue())["commands"]


def test_describe_command_runs_single_command_text_and_json() -> None:
    """`DescribeCommand` writes one command's text or JSON and returns 0."""
    # Given parsed arguments for `describe config` and `describe config --json`
    text_io, text_out = _stdio()
    json_io, json_out = _stdio()
    cmd = DescribeCommand()

    # When run for text and JSON
    text_code = cmd.run(_parse(["config"]), text_io)
    json_code = cmd.run(_parse(["config", "--json"]), json_io)

    # Then both succeed and include config details
    assert text_code == 0
    assert json_code == 0
    assert "wio config -" in text_out.getvalue()
    assert json.loads(json_out.getvalue())["name"] == "config"


def test_describe_command_raises_wio_error_on_unknown_command() -> None:
    """`DescribeCommand` raises `WioError` when the command name is unknown."""
    # Given parsed arguments with an unknown command
    args = _parse(["nosuch"])
    fake_io, _ = _stdio()

    # When DescribeCommand.run is called
    with pytest.raises(WioError, match="nosuch"):
        DescribeCommand().run(args, fake_io)

    # Then WioError is raised for the CLI dispatcher to exit 2
