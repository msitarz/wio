# SPDX-License-Identifier: Apache-2.0
"""Tests of what `wio.cli` gives `wio context`."""

from typing import TYPE_CHECKING

import pytest

from tests.support import enter, git
from wio.cli import main
from wio.cli.table import _context
from wio.io.adapters import SystemStdio

if TYPE_CHECKING:
    from tests.sandbox import Sandbox


def test_context_reads_the_project_through_the_adapters() -> None:
    """The entry wires the shell over the adapters of `wio.io` and `wio.env`."""
    # Given no setup

    # When `wio.cli` wires `wio context`; `tests.integration` may not import
    # `wio.context`, so the services are reached by their public name
    services = getattr(_context(), "services")  # noqa: B009
    found = [
        type(services.repository).__name__,
        type(services.files).__name__,
        type(services.environment).__name__,
    ]

    # Then they are the real adapters
    assert found == ["GitRepository", "LocalFileSystem", "ProcessEnvironment"]


@pytest.mark.slow
@pytest.mark.xfail(strict=True)
def test_a_run_says_that_no_bundle_can_be_composed_yet(
    sandbox: Sandbox,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Without a composition a run is refused, and is not taken for a bug."""
    # Given a repository, entered as the working directory
    git(sandbox, "init", "-q", check=True)
    enter(sandbox, monkeypatch)

    # When `wio context` runs
    code = main(["context", "k3m9xq", "deliver", "architecture"], SystemStdio())

    # Then it exits 2, says why on standard error and prints no bundle
    out, err = capsys.readouterr()
    assert (code, out) == (2, "")
    assert err == "error: wio context cannot compose a bundle yet\n"
