# SPDX-License-Identifier: Apache-2.0
"""Test log integration at the real adapter and codec boundaries.

The scenarios check what the console command and a future context producer
leave on disk, including records from concurrent command invocations.
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from math import floor
from pathlib import Path
from threading import Barrier
from time import time
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.drivers.cli import CliDriver
from tests.support import enter, git
from wio.env.adapters import ProcessDirectories, ProcessEnvironment, SystemClock
from wio.formats.event_lines import decode_lines, format_event_time
from wio.io.adapters import GitRepository, LocalFileSystem, SystemStdio
from wio.log.sink import LogSink
from wio.models.config import Log
from wio.models.events import ContextEvent, ReviewEvent
from wio.models.frozen import freeze

if TYPE_CHECKING:
    from tests.acceptance.drivers.base import RunResult
    from tests.sandbox import Sandbox

_REVIEW = ["trailers", "k3m9xq", "deliver", "architecture-review", "--result", "pass"]


@pytest.fixture
def driver(sandbox: Sandbox) -> CliDriver:
    """Initialize an isolated clone and real console driver.

    Args:
        sandbox: The clone's directory and environment.

    Returns:
        A CLI driver whose clone contains a reviewable Work.
    """
    driver = CliDriver(sandbox)
    driver.install("trailers/command")
    git(sandbox, "add", "-A", check=True)
    git(sandbox, "commit", "-m", "feat: add the reviewed artifact", check=True)
    Path(sandbox.env["WIO_HOME"]).mkdir()
    return driver


def _event_text(sandbox: Sandbox) -> str:
    """Read the event log written by the isolated clone.

    Args:
        sandbox: The environment with the clone's Wio home.

    Returns:
        The complete contents of the clone's events file.
    """
    home = Path(sandbox.env["WIO_HOME"])
    (path,) = (home / "log").glob("*/events.jsonl")
    return path.read_text(encoding="utf-8")


@pytest.mark.slow
def test_review_stamp_uses_real_clock_and_subdirectory(
    driver: CliDriver, sandbox: Sandbox
) -> None:
    """AC-2 stamps the time and working directory of a real command.

    Args:
        driver: Runs the installed command in a subdirectory.
        sandbox: Supplies the clone and its Wio home.
    """
    # Given a subdirectory of the real clone.
    subdirectory = sandbox.root / "nested"
    subdirectory.mkdir()

    # When the review command starts from the subdirectory.
    before = time()
    outcome = driver.run(_REVIEW, directory="nested")
    after = time()

    # Then the decoded envelope records that directory and a time in the window.
    assert outcome.exit_code == 0
    decoded = decode_lines(_event_text(sandbox))
    assert decoded.skipped == 0
    (entry,) = decoded.entries
    assert Path(entry.envelope.directory).resolve() == subdirectory.resolve()
    assert (
        floor(before * 1000) <= round(entry.envelope.time * 1000) <= floor(after * 1000)
    )


@pytest.mark.slow
@pytest.mark.usefixtures("driver")
def test_concurrent_processes_write_whole_event_lines(
    sandbox: Sandbox,
) -> None:
    """AC-5 preserves each append from concurrent subprocesses.

    Args:
        sandbox: Supplies their shared Wio home.
    """
    # Given twenty command invocations that share a launch barrier.
    writers = 20
    start = Barrier(writers, timeout=30)

    def record(writer: int) -> RunResult:
        """Release the subprocess launch together with the other writers.

        Args:
            writer: Distinguishes this process in the recorded session fields.

        Returns:
            The output and status of this process.
        """
        isolated = replace(
            sandbox, env=sandbox.env | {"CLAUDE_CODE_SESSION_ID": f"writer-{writer}"}
        )
        start.wait()
        return CliDriver(isolated).run(_REVIEW)

    # When all writers record a review concurrently.
    with ThreadPoolExecutor(max_workers=writers) as pool:
        jobs = [pool.submit(record, writer) for writer in range(writers)]
        outcomes = [job.result() for job in jobs]

    # Then all processes succeed, and each wrote one whole review line.
    assert all(result.exit_code == 0 and not result.stderr for result in outcomes)
    text = _event_text(sandbox)
    assert text.count("\n") == writers
    decoded = decode_lines(text)
    assert decoded.skipped == 0
    assert len(decoded.entries) == writers
    assert all(isinstance(entry.event, ReviewEvent) for entry in decoded.entries)
    assert {entry.envelope.session for entry in decoded.entries} == {
        f"writer-{writer}" for writer in range(writers)
    }


@pytest.mark.slow
def test_real_sink_round_trips_a_complete_context(
    driver: CliDriver,
    sandbox: Sandbox,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-6 round-trips all context fields through real ports and log show.

    Args:
        driver: Runs the installed log reader against the written event.
        sandbox: Supplies the repository and isolated Wio home.
        monkeypatch: Applies the sandbox environment to the real sink.
    """
    # Given a gate context with ordered rule hashes and all optional fields.
    enter(sandbox, monkeypatch)
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "c1")
    environment = ProcessEnvironment()
    sink = LogSink(
        environment,
        SystemClock(),
        ProcessDirectories(environment),
        GitRepository(environment),
        LocalFileSystem(),
        SystemStdio(),
        Log(),
    )
    context = ContextEvent(
        work="k3m9xq",
        action="deliver",
        stage="architecture-review",
        bundle="bundle",
        size=32,
        rules=freeze({"docs.DOC002": "b" * 64, "docs.DOC001": "a" * 64}),
        start="f" * 40,
        dirty=True,
    )

    # When the real sink writes it and log show reads it.
    sink.write(context)
    shown = driver.run(["log", "show", context.work])

    # Then the stored event retains all fields and the display shows its time.
    assert (shown.exit_code, shown.stderr) == (0, "")
    decoded = decode_lines(_event_text(sandbox))
    assert decoded.skipped == 0
    (entry,) = decoded.entries
    assert isinstance(entry.event, ContextEvent)
    assert entry.event == context
    assert tuple(entry.event.rules.items()) == tuple(context.rules.items())
    stamp = format_event_time(entry.envelope.time)
    assert shown.stdout == (
        f"{context.work}\n  {context.action} {context.stage}"
        f"  entered {stamp}  claude-code:c1\n"
    )
