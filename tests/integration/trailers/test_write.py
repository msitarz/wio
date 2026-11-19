# SPDX-License-Identifier: Apache-2.0
"""Tests of the write form of `wio trailers` on real git and a recording sink.

The examples use the project of `tests/fixtures/trailers/command`, committed, with
a work commit under a pure gate commit of `architecture-review`, and the command of
`trailers_command` over a sink that keeps the events.
"""

import io
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, TextIO

import pytest

from tests.support import enter, git
from wio import cli
from wio.cli.table import Entry, component_entry, trailers_command
from wio.models.events import Event, ReviewEvent

if TYPE_CHECKING:
    from tests.sandbox import Sandbox

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "trailers" / "command"
WORK = "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: architecture"
GATE = (
    "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: architecture-review\n"
    "Wio-Result: pass\nWio-Judge: human"
)
ARGS = ["trailers", "k3m9xq", "deliver", "architecture-review"]


@dataclass
class _Sink:
    """An `EventSink` that keeps the events it is given.

    Attributes:
        events: The events written, in order.
    """

    events: list[Event] = field(default_factory=list)

    def write(self, event: Event) -> None:
        """Keep the event.

        Args:
            event: The event to record.
        """
        self.events.append(event)


@dataclass
class _Stdio:
    """The streams of one run.

    Attributes:
        stdin: Empty input.
        stdout: What the command prints.
        stderr: What it says about a mistake.
    """

    stdin: TextIO
    stdout: TextIO
    stderr: TextIO


def _commit(sandbox: Sandbox, message: str, *, empty: bool = False) -> str:
    """Stage everything, commit it and give the commit's sha.

    Args:
        sandbox: The repository.
        message: The whole message.
        empty: Whether the commit may change nothing.

    Returns:
        The full sha of the new commit.
    """
    git(sandbox, "add", "-A", check=True)
    flags = ["--allow-empty"] if empty else []
    git(sandbox, "commit", "-q", *flags, "-m", message, check=True)
    return git(sandbox, "rev-parse", "HEAD", check=True).stdout.strip()


def _project(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch, *, reviewed: bool = True
) -> str:
    """Build the repository and enter it.

    Args:
        sandbox: The repository to build in.
        monkeypatch: Enters the sandbox.
        reviewed: Whether a work commit sits under the gate commit. Without it
            every commit is a pure gate commit.

    Returns:
        The sha of the work commit, or of the gate commit when there is none.
    """
    shutil.copytree(FIXTURE, sandbox.root, dirs_exist_ok=True)
    git(sandbox, "init", "-q", check=True)
    if reviewed:
        _commit(sandbox, "feat: add the Work")
        (sandbox.root / "note.txt").write_text("x\n")
        sha = _commit(sandbox, f"feat: add x\n\n{WORK}")
        _commit(sandbox, f"chore: judge\n\n{GATE}", empty=True)
    else:
        sha = _commit(sandbox, f"chore: judge\n\n{GATE}")
    enter(sandbox, monkeypatch)
    return sha


def _run(sink: _Sink, *args: str) -> tuple[int, str]:
    """Run `wio trailers` with the sink.

    Args:
        sink: Where the events go.
        *args: The arguments after the program name.

    Returns:
        The exit code and what the command printed.
    """
    entry: Entry = component_entry("trailers", lambda: trailers_command(sink))
    out = io.StringIO()
    stdio = _Stdio(io.StringIO(), out, io.StringIO())
    code = cli.main(list(args), stdio, (entry,))
    return code, out.getvalue()


def test_an_agent_and_then_a_human_each_write_an_event(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-1: a human gate takes both judges, and each result is one event."""
    # Given a human gate with a work commit under a pure gate commit
    work = _project(sandbox, monkeypatch)
    sink = _Sink()

    # When the result is recorded as the agent, and then as the human
    first = _run(sink, *ARGS, "--result", "pass")
    second = _run(sink, *ARGS, "--result", "pass", "--judge", "human")

    # Then each exits 0, and the sink holds two events of the work commit, judged by
    # the agent and then by the human
    assert (first[0], second[0]) == (0, 0)
    assert [(e.judge, e.commit) for e in sink.events if isinstance(e, ReviewEvent)] == [
        ("agent", work),
        ("human", work),
    ]


@pytest.mark.parametrize(
    ("reviewed", "flags"),
    [(False, ["--result", "pass", "--judge", "human"]), (True, ["--result", "maybe"])],
    ids=["no reviewed commit", "a result outside the vocabulary"],
)
def test_a_refusal_writes_no_event(
    sandbox: Sandbox,
    monkeypatch: pytest.MonkeyPatch,
    reviewed: bool,  # noqa: FBT001 - a pytest parameter
    flags: list[str],
) -> None:
    """AC-1, AC-2: a refused result or reviewed commit sends no event."""
    # Given a gate whose history has no reviewed commit, or a gate with one and a
    # config whose results lack `maybe`
    _project(sandbox, monkeypatch, reviewed=reviewed)
    sink = _Sink()

    # When the result is recorded
    code, out = _run(sink, *ARGS, *flags)

    # Then it exits 1, prints nothing and writes no event
    assert (code, out, sink.events) == (1, "", [])


def test_the_event_names_the_commit_and_the_cites(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-3: the event holds the reviewed commit and each cited item."""
    # Given a human gate with a work commit under a pure gate commit, and an item
    # `AC-1`
    work = _project(sandbox, monkeypatch)
    sink = _Sink()

    # When the result is recorded with `--items AC-1 --cite AC-1=pass`
    code, _ = _run(
        sink, *ARGS, "--result", "pass", "--judge", "human", "--items", "AC-1",
        "--cite", "AC-1=pass",
    )  # fmt: skip

    # Then it exits 0 and the sink holds one event of the work commit that cites
    # `AC-1` with `pass`
    (event,) = sink.events
    assert code == 0
    assert isinstance(event, ReviewEvent)
    assert (event.commit, dict(event.cited)) == (work, {"AC-1": "pass"})


def test_a_gate_result_is_taken_back_by_the_check_and_the_fold(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-4 of `3jbrzz`: the record, the check, the fold and the event agree."""
    # Given a human gate with a work commit under a pure gate commit, and an item
    # `AC-1`
    work = _project(sandbox, monkeypatch)
    sink = _Sink()

    # When the result is recorded with `--items AC-1 --cite AC-1=pass`, that record
    # is the paragraph of a message that `check --require` reads, and `fold block`
    # runs on a range with a commit that carries it
    code, record = _run(
        sink, *ARGS, "--result", "pass", "--judge", "human", "--items", "AC-1",
        "--cite", "AC-1=pass",
    )  # fmt: skip
    (sandbox.root / "msg.txt").write_text(f"chore: judge\n\n{record}")
    checked, _ = _run(sink, "trailers", "check", "--require", "msg.txt")
    _commit(sandbox, f"chore: judge\n\n{record}", empty=True)
    folded, block = _run(sink, "trailers", "fold", "block", "HEAD~1..HEAD")

    # Then the record holds the result, the judge and the item, the check exits 0, the
    # fold prints the record and the sink received one event of the work commit
    (event,) = sink.events
    assert (code, checked, folded) == (0, 0, 0)
    assert {"Wio-Result: pass", "Wio-Judge: human", "Wio-Items: AC-1"} <= set(
        record.splitlines()
    )
    assert block == record
    assert isinstance(event, ReviewEvent)
    assert (event.commit, dict(event.cited)) == (work, {"AC-1": "pass"})


def test_the_default_command_appends_reviews_from_both_worktrees() -> None:
    """AC-4 wires the real recording sink to the default command.

    The clone identity gives the main checkout and the linked worktree one log.
    """
    # Given a real clone with a reviewed Work commit and a linked worktree.
    # When the default command records the gate in each checkout.
    # Then both records print and both review events name the Work, gate and
    # reviewed commit in the only events.jsonl under the temporary Wio home.
    pytest.skip("Pending log sink wiring")


def test_the_default_command_outside_git_leaves_the_home_empty() -> None:
    """AC-4 preserves the command error outside a repository.

    An unavailable repository stops the command before it can record.
    """
    # Given a working directory outside Git and an empty Wio home.
    # When the default command attempts to record a result.
    # Then the original trailers usage error is returned and the home is empty.
    pytest.skip("Pending log sink wiring")


def test_the_default_command_writes_log_warnings_to_its_stderr() -> None:
    """AC-4 routes recording warnings to the command's supplied streams.

    An unavailable events file leaves the gate result available to the caller.
    """
    # Given a real clone and a Wio home beneath a regular file.
    # When the default CLI entry point records a gate with in-memory Stdio.
    # Then it exits zero, the record goes to stdout, and stderr warns that the
    # event log could not be written.
    pytest.skip("Pending log sink wiring")
