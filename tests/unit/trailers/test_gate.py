# SPDX-License-Identifier: Apache-2.0
"""Tests of the gate form of `wio trailers`, run with fakes of its ports.

The examples use a Work `k3m9xq`, hypothetical, with the items `AC-1` and `AC-3`,
and the action `deliver`. The gate `docs-review` has `judge = "human"`, and the
stage rules port, faked, gives `docs.DOC001` with the hash `h1` for it and no
`contracts.CON001`. A recording `EventSink` is injected, and the history holds a
work commit under a pure gate commit.
"""

import io
from argparse import ArgumentParser
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, cast, override

import pytest

from tests.unit.fakes import FakeFirstParents, FakeRules, FakeStdio, RecordingSink
from tests.unit.trailers.test_check import Settings
from tests.unit.trailers.test_fold import _commit, _id
from tests.unit.trailers.test_reviewed import WORK
from tests.unit.trailers.test_validation import CONFIG, FakeContracts
from wio.models.config import Stage
from wio.models.events import ReviewEvent
from wio.models.frozen import freeze
from wio.trailers import Services
from wio.trailers.write import configure_write, run_write

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.io.ports import FileSystem, History
    from wio.models.commits import Commit

STAGES = {
    **CONFIG.stages,
    "docs-review": Stage(goal="d", gate=True, judge="human"),
    "system-review": Stage(goal="s", gate=True),
}
GATE_CONFIG = replace(CONFIG, stages=freeze(STAGES))
DOCS = ["k3m9xq", "deliver", "docs-review"]
GATE_RECORD = (
    "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: docs-review\n"
    "Wio-Result: pass\nWio-Judge: human"
)
PIPELINE = ["architecture", "architecture-review", "docs-review"]


@dataclass(frozen=True)
class GateContracts(FakeContracts):
    """The `Contracts` port whose `deliver` also lists `docs-review`."""

    @override
    def pipeline(self, work_id: str, action: str) -> Sequence[str] | None:
        """Find the stages of a Work's action.

        Args:
            work_id: The Work's id.
            action: The action.

        Returns:
            The stages of `deliver` for `k3m9xq`, which include `docs-review`.
        """
        if work_id == "k3m9xq" and action == "deliver":
            return PIPELINE
        return super().pipeline(work_id, action)


def _history(*commits: Commit) -> History:
    """Make a history of commits from the oldest.

    Args:
        *commits: The commits.

    Returns:
        A `History` port that gives them newest first.
    """
    return cast("History", FakeFirstParents(commits))


WORK_ABOVE_GATE = (_commit(1, WORK), _commit(2, GATE_RECORD))


def _run(
    argv: list[str],
    *,
    sink: RecordingSink | None = None,
    history: History | None = None,
) -> tuple[int, str, str, RecordingSink]:
    """Run the form on the arguments.

    Args:
        argv: The arguments after `wio trailers`.
        sink: The `EventSink`, or `None` for a recording one.
        history: The `History` port, or `None` for the work commit `c1` under the
            pure gate commit `c2`.

    Returns:
        The exit code, standard output, standard error and the sink.
    """
    parser = ArgumentParser(prog="wio trailers")
    configure_write(parser)
    args = parser.parse_args(argv)
    out, err = io.StringIO(), io.StringIO()
    events = sink or RecordingSink(stderr=err)
    services = Services(
        Settings(GATE_CONFIG),
        GateContracts(),
        history or _history(*WORK_ABOVE_GATE),
        GateContracts(),
        cast("FileSystem", object()),
        FakeRules({("k3m9xq", "deliver", "docs-review"): {"docs.DOC001": "h1"}}),
        events,
    )
    code = run_write(services, args, FakeStdio(stdout=out, stderr=err))
    return code, out.getvalue(), err.getvalue(), events


def _event(judge: str, result: str, cited: dict[str, str]) -> ReviewEvent:
    """Build the event of a review of `docs-review` that judged `c1`.

    Args:
        judge: Who judged.
        result: The overall result.
        cited: What the review cited, each with its result.

    Returns:
        The event, with the hash `h1` for `docs.DOC001`.
    """
    hashes = {key: "h1" for key in cited if key == "docs.DOC001"}
    return ReviewEvent(
        "k3m9xq", "deliver", "docs-review", _id(1), judge, result, cited, hashes
    )


def test_a_human_gate_holds_the_result_of_an_agent_and_of_a_human() -> None:
    """AC-1: two events, the first judged by an agent and the second by a human."""
    # Given `k3m9xq` and `docs-review`
    sink = RecordingSink()

    # When `wio trailers k3m9xq deliver docs-review --result pass` runs, and then
    # again with `--judge human`
    first = _run([*DOCS, "--result", "pass"], sink=sink)
    second = _run([*DOCS, "--result", "pass", "--judge", "human"], sink=sink)

    # Then each exits 0; the first prints `Wio-Judge: agent` and the second
    # `Wio-Judge: human`, and the sink receives two events, the first with the judge
    # `agent` and the second with the judge `human`
    assert first[0] == second[0] == 0
    assert first[1].endswith("Wio-Judge: agent\n")
    assert second[1].endswith("Wio-Judge: human\n")
    assert [e.judge for e in sink.events if isinstance(e, ReviewEvent)] == [
        "agent",
        "human",
    ]


def test_an_agent_that_fails_the_gate_records_a_fail() -> None:
    """AC-1: `--result fail --judge agent` is recorded and printed."""
    # Given the same gate
    # When the command runs with `--result fail --judge agent`
    code, out, _, sink = _run([*DOCS, "--result", "fail", "--judge", "agent"])

    # Then it exits 0, prints `Wio-Result: fail` and `Wio-Judge: agent`, and the
    # sink receives one event with the result `fail`
    assert code == 0
    assert "Wio-Result: fail\n" in out
    assert out.endswith("Wio-Judge: agent\n")
    assert sink.events == [_event("agent", "fail", {})]


@pytest.mark.parametrize(
    ("cites", "name"),
    [
        (["contracts.CON001=fail"], "contracts.CON001"),
        (["AC-99=pass"], "AC-99"),
        (["AC-1=maybe"], "AC-1"),
        (["AC-1"], "--cite"),
        (["=pass"], "--cite"),
        (["AC-1="], "--cite"),
        (["AC-1=pass", "AC-1=fail"], "AC-1"),
        (["DOC001=fail"], "DOC001"),
    ],
    ids=[
        "unselected",
        "no-item",
        "result",
        "no-equals",
        "no-key",
        "no-result",
        "repeated",
        "unqualified",
    ],
)
def test_a_cite_that_is_refused_writes_no_event(cites: list[str], name: str) -> None:
    """AC-2: each refusal exits 1, names its key and gives the sink no event."""
    # Given `k3m9xq` and the gate `docs-review`
    # When `wio trailers k3m9xq deliver docs-review --result pass --judge human` runs
    # with each of `--cite contracts.CON001=fail`, `--cite AC-99=pass`,
    # `--cite AC-1=maybe`, `--cite AC-1`, `--cite =pass`, `--cite AC-1=`,
    # `--cite AC-1=pass --cite AC-1=fail` and `--cite DOC001=fail`
    argv = [*DOCS, "--result", "pass", "--judge", "human"]
    for cite in cites:
        argv += ["--cite", cite]
    code, out, err, sink = _run(argv)

    # Then each exits 1, prints nothing on standard output and prints on standard
    # error an `error:` line that names, in turn, `contracts.CON001`, `AC-99`,
    # `AC-1`, `--cite`, `--cite`, `--cite`, `AC-1` and `DOC001`, and the sink
    # receives no event
    assert code == 1
    assert out == ""
    assert f"error: {name}:" in err
    assert sink.events == []


def test_a_cite_without_a_result_is_refused() -> None:
    """AC-2: `--cite` on a stage that is not a gate needs a `--result`."""
    # Given `k3m9xq` and the stage `architecture`, which is not a gate
    # When `wio trailers k3m9xq deliver architecture --cite AC-1=pass` runs
    code, out, err, sink = _run(
        ["k3m9xq", "deliver", "architecture", "--cite", "AC-1=pass"]
    )

    # Then it exits 1, prints nothing on standard output and prints
    # `error: --cite:` on standard error
    assert code == 1
    assert out == ""
    assert err.startswith("error: --cite:")
    assert sink.events == []


def test_a_cite_that_is_accepted_is_in_the_event() -> None:
    """AC-2: `AC-1` and `docs.DOC001` with its hash `h1` are cited."""
    # Given `k3m9xq` and the gate `docs-review`
    # When the command runs with `--result pass --judge human --cite AC-1=pass
    # --cite docs.DOC001=fail`
    argv = [*DOCS, "--result", "pass", "--judge", "human"]
    code, _, _, sink = _run(
        [*argv, "--cite", "AC-1=pass", "--cite", "docs.DOC001=fail"]
    )

    # Then it exits 0 and the sink receives one event that cites `AC-1` with `pass`
    # and `docs.DOC001` with `fail` and the hash `h1`
    assert code == 0
    cited = {"AC-1": "pass", "docs.DOC001": "fail"}
    assert sink.events == [_event("human", "pass", cited)]


def test_the_event_names_the_reviewed_commit_and_the_judgment() -> None:
    """AC-3: the full sha of `c1`, under the pure gate commit `c2`."""
    # Given `k3m9xq`, a history of the pure gate commit `c2` above the work commit
    # `c1`, and the recording `EventSink`
    # When `wio trailers k3m9xq deliver docs-review --result pass --judge human
    # --cite AC-1=pass` runs
    argv = [*DOCS, "--result", "pass", "--judge", "human", "--cite", "AC-1=pass"]
    _, _, _, sink = _run(argv)

    # Then the sink receives one event with `k3m9xq`, `deliver`, `docs-review`, the
    # full sha of `c1`, the judge `human`, the result `pass` and `AC-1` with `pass`
    assert sink.events == [_event("human", "pass", {"AC-1": "pass"})]


def test_a_history_with_no_reviewed_commit_writes_no_event() -> None:
    """AC-3: `error: Wio-Work: no reviewed commit was found`, and no event."""
    # Given a history of commits that each carry only a gate record
    history = _history(_commit(1, GATE_RECORD), _commit(2, GATE_RECORD))

    # When the same command runs
    argv = [*DOCS, "--result", "pass", "--judge", "human", "--cite", "AC-1=pass"]
    code, out, err, sink = _run(argv, history=history)

    # Then it exits 1, prints nothing on standard output, prints
    # `error: Wio-Work: no reviewed commit was found` on standard error and the sink
    # receives no event
    assert code == 1
    assert out == ""
    assert "error: Wio-Work: no reviewed commit was found\n" in err
    assert sink.events == []


def test_a_stage_outside_the_pipeline_is_a_warning_and_the_event_is_written() -> None:
    """AC-4: the warning names `system-review`, and the sink gets one event."""
    # Given the gate `system-review`, which is outside the `typed-boundary` preset
    # that is `k3m9xq`'s `deliver`
    # When `wio trailers k3m9xq deliver system-review --result pass` runs
    code, _, err, sink = _run(
        ["k3m9xq", "deliver", "system-review", "--result", "pass"]
    )

    # Then it prints a warning naming `system-review` on standard error, exits 0 and
    # the sink receives one event
    assert code == 0
    assert "warning:" in err
    assert "system-review" in err
    assert len(sink.events) == 1


def test_a_failing_sink_never_fails_the_command() -> None:
    """AC-5: the sink's warning, the record and exit 0."""
    # Given a sink whose write fails and which reports the failure itself as a
    # warning on standard error, without raising, as the `EventSink` port says
    err = io.StringIO()
    sink = RecordingSink(warning="the event log cannot be written", stderr=err)

    # When `wio trailers k3m9xq deliver docs-review --result pass --judge human` runs
    code, out, errors, _ = _run(
        [*DOCS, "--result", "pass", "--judge", "human"], sink=sink
    )

    # Then the warning of the sink is on standard error, the record is on standard
    # output and the command exits 0
    assert code == 0
    assert out.startswith("Wio-Work: k3m9xq\n")
    assert "warning: the event log cannot be written" in err.getvalue() + errors
