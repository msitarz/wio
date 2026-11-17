# SPDX-License-Identifier: Apache-2.0
"""Tests of the gate form of `wio trailers`, run with fakes of its ports.

Each test is a stub for one scenario of the Work that records a gate's result, and
skips until the implementation stage fills it in. The examples use a Work `k3m9xq`,
hypothetical, with the items `AC-1` and `AC-3`, and the action `deliver`. The gate
`docs-review` has `judge = "human"`, and the stage rules port, faked, gives
`docs.DOC001` with the hash `h1` for it and no `contracts.CON001`. A recording
`EventSink` is injected, and the history holds a work commit under a pure gate
commit.
"""

import pytest

STUB = "filled in by the implementation stage"


def test_a_human_gate_holds_the_result_of_an_agent_and_of_a_human() -> None:
    """AC-1: two events, the first judged by an agent and the second by a human."""
    # Given `k3m9xq` and `docs-review`
    # When `wio trailers k3m9xq deliver docs-review --result pass` runs, and then
    # again with `--judge human`
    # Then each exits 0; the first prints `Wio-Judge: agent` and the second
    # `Wio-Judge: human`, and the sink receives two events, the first with the judge
    # `agent` and the second with the judge `human`
    pytest.skip(STUB)


def test_an_agent_that_fails_the_gate_records_a_fail() -> None:
    """AC-1: `--result fail --judge agent` is recorded and printed."""
    # Given the same gate
    # When the command runs with `--result fail --judge agent`
    # Then it exits 0, prints `Wio-Result: fail` and `Wio-Judge: agent`, and the
    # sink receives one event with the result `fail`
    pytest.skip(STUB)


@pytest.mark.parametrize(
    "cite",
    [
        "contracts.CON001=fail",
        "AC-99=pass",
        "AC-1=maybe",
        "AC-1",
        "=pass",
        "AC-1=",
        "AC-1=pass --cite AC-1=fail",
        "DOC001=fail",
    ],
)
def test_a_cite_that_is_refused_writes_no_event(cite: str) -> None:
    """AC-2: each refusal exits 1, names its key and gives the sink no event."""
    # Given `k3m9xq` and the gate `docs-review`
    # When `wio trailers k3m9xq deliver docs-review --result pass --judge human` runs
    # with each of `--cite contracts.CON001=fail`, `--cite AC-99=pass`,
    # `--cite AC-1=maybe`, `--cite AC-1`, `--cite =pass`, `--cite AC-1=`,
    # `--cite AC-1=pass --cite AC-1=fail` and `--cite DOC001=fail`
    # Then each exits 1, prints nothing on standard output and prints on standard
    # error an `error:` line that names, in turn, `contracts.CON001`, `AC-99`,
    # `AC-1`, `--cite`, `--cite`, `--cite`, `AC-1` and `DOC001`, and the sink
    # receives no event
    pytest.skip(f"{STUB}: {cite}")


def test_a_cite_without_a_result_is_refused() -> None:
    """AC-2: `--cite` on a stage that is not a gate needs a `--result`."""
    # Given `k3m9xq` and the stage `architecture`, which is not a gate
    # When `wio trailers k3m9xq deliver architecture --cite AC-1=pass` runs
    # Then it exits 1, prints nothing on standard output and prints
    # `error: --cite:` on standard error
    pytest.skip(STUB)


def test_a_cite_that_is_accepted_is_in_the_event() -> None:
    """AC-2: `AC-1` and `docs.DOC001` with its hash `h1` are cited."""
    # Given `k3m9xq` and the gate `docs-review`
    # When the command runs with `--result pass --judge human --cite AC-1=pass
    # --cite docs.DOC001=fail`
    # Then it exits 0 and the sink receives one event that cites `AC-1` with `pass`
    # and `docs.DOC001` with `fail` and the hash `h1`
    pytest.skip(STUB)


def test_the_event_names_the_reviewed_commit_and_the_judgment() -> None:
    """AC-3: the full sha of `c1`, under the pure gate commit `c2`."""
    # Given `k3m9xq`, a history of the pure gate commit `c2` above the work commit
    # `c1`, and the recording `EventSink`
    # When `wio trailers k3m9xq deliver docs-review --result pass --judge human
    # --cite AC-1=pass` runs
    # Then the sink receives one event with `k3m9xq`, `deliver`, `docs-review`, the
    # full sha of `c1`, the judge `human`, the result `pass` and `AC-1` with `pass`
    pytest.skip(STUB)


def test_a_history_with_no_reviewed_commit_writes_no_event() -> None:
    """AC-3: `error: Wio-Work: no reviewed commit was found`, and no event."""
    # Given a history of commits that each carry only a gate record
    # When the same command runs
    # Then it exits 1, prints nothing on standard output, prints
    # `error: Wio-Work: no reviewed commit was found` on standard error and the sink
    # receives no event
    pytest.skip(STUB)


def test_a_stage_outside_the_pipeline_is_a_warning_and_the_event_is_written() -> None:
    """AC-4: the warning names `system-review`, and the sink gets one event."""
    # Given the gate `system-review`, which is outside the `typed-boundary` preset
    # that is `k3m9xq`'s `deliver`
    # When `wio trailers k3m9xq deliver system-review --result pass` runs
    # Then it prints a warning naming `system-review` on standard error, exits 0 and
    # the sink receives one event
    pytest.skip(STUB)


def test_a_failing_sink_never_fails_the_command() -> None:
    """AC-5: the sink's warning, the record and exit 0."""
    # Given a sink whose write fails and which reports the failure itself as a
    # warning on standard error, without raising, as the `EventSink` port says
    # When `wio trailers k3m9xq deliver docs-review --result pass --judge human` runs
    # Then the warning of the sink is on standard error, the record is on standard
    # output and the command exits 0
    pytest.skip(STUB)
