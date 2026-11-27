# SPDX-License-Identifier: Apache-2.0
"""System scenarios for delivering context bundles and reporting warnings."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox

_CONFIG = ".agents/wio/config.toml"
_ARGS = ["context", "k3m9xq", "deliver", "implementation"]


def _with_threshold(wio: Wio, fixture: str, threshold: int) -> None:
    """Install a sample repository with a configured bundle size threshold.

    Args:
        wio: The scenario's facade.
        fixture: The context fixture name to install.
        threshold: The threshold in UTF-8 bytes to prepend to the config.
    """
    wio.fixture(fixture)
    header = f"[bundle]\nsize_threshold = {threshold}\n".encode()
    wio.put(_CONFIG, header + wio.read(_CONFIG))


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_size_warning_is_identical_for_stdout_and_file_delivery(
    wio: Wio, sandbox: Sandbox
) -> None:
    """AC-1: an oversized body reports the same warning to stdout and a file."""
    # Given a threshold below the bundle body and an external temporary directory
    _with_threshold(wio, "context/unreadable", 1)
    sandbox.env["TMPDIR"] = str(sandbox.root.parent / "temp")

    # When the bundle is delivered to standard output and then to the default file
    stdout_run = wio.run(_ARGS)
    file_run = wio.run([*_ARGS, "--output"])

    # Then both runs succeed and emit the exact same size warning
    assert (stdout_run.exit_code, file_run.exit_code) == (0, 0)
    assert stdout_run.stderr.startswith("warning: Bundle body size (bytes): ")
    assert file_run.stderr == stdout_run.stderr
    written = Path(file_run.stdout.strip())
    assert file_run.stdout == f"{written}\n"
    assert written.read_text(encoding="utf-8") == stdout_run.stdout


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_failed_write_reports_size_warning_before_error(wio: Wio) -> None:
    """AC-2: a failed file delivery still reports the size warning first."""
    # Given a threshold below the bundle body and an unwritable output path
    _with_threshold(wio, "context/unreadable", 1)

    # When the command tries to write the bundle to a directory path
    result = wio.run([*_ARGS, "--output", "."])

    # Then the size warning precedes the error and no bundle is printed
    assert (result.exit_code, result.stdout) == (2, "")
    lines = result.stderr.splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("warning: Bundle body size (bytes): ")
    assert lines[0].endswith("threshold (bytes): 1.")
    assert lines[1].startswith("error: ")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_warnings_are_reported_in_order(wio: Wio) -> None:
    """AC-3: compiler, size, and worktree-path warnings appear in that order."""
    # Given a stage outside the pipeline, a small threshold, and an inside path
    _with_threshold(wio, "context/pipeline", 1)

    # When the bundle is delivered to a path inside the repository root
    result = wio.run(
        ["context", "a1b2c3", "deliver", "define", "--output", "inside.md"]
    )

    # Then all three warnings appear in order, naming the size of the written body
    assert (result.exit_code, result.stdout) == (0, "inside.md\n")
    text = wio.read("inside.md").decode("utf-8")
    body = text.split("\n\n", 2)[2]
    body_size = len(body.encode("utf-8"))
    assert result.stderr.splitlines() == [
        "warning: The stage `define` is not in the `deliver` pipeline of `a1b2c3`.",
        f"warning: Bundle body size (bytes): {body_size}; threshold (bytes): 1.",
        "warning: The uncommitted bundle can be committed by mistake.",
    ]
