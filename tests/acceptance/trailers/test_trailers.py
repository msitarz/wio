# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio trailers` as a whole, one for each example of the top Work.

The scenarios use the project of `test_command.py`: a git repository whose config
declares the stages `architecture` and `architecture-review`, a gate that needs a
human, and a Work `k3m9xq` that has an item `AC-1`. They run on the CLI channel
only, because the forms read the history, the index and `HEAD` of a git
repository. The `review` event reaches a sink that the CLI wires to nothing, so
the event of the gate's result is asserted in
`tests/integration/trailers/test_write.py`. AC-6, the round trip on a real
repository, is `test_a_record_round_trips_through_the_real_adapters` of
`test_command.py`.
"""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

FIXTURE = "trailers/command"
WORK = ["k3m9xq", "deliver"]
RECORD = "Wio-Work: {work}\nWio-Action: deliver\nWio-Stage: {stage}"
CHILD = "a7b2c4"
PARENT = "p9x2wq"


def _project(wio: Wio) -> None:
    """Start from the project, committed, so that the Work is in `HEAD`.

    Args:
        wio: The facade.
    """
    wio.fixture(FIXTURE)
    wio.commit("feat: add the Work")


def _deliver(wio: Wio, work: str, stage: str) -> None:
    """Commit a record of a delivery that changes nothing.

    Args:
        wio: The facade.
        work: The id the record names.
        stage: The stage the record names.
    """
    wio.commit(f"chore: step\n\n{RECORD.format(work=work, stage=stage)}", empty=True)


@pytest.mark.channels(Channel.CLI)
def test_a_written_record_is_accepted_by_check(wio: Wio) -> None:
    """AC-1: the record that is printed is the record that the check accepts."""
    # Given a Work in the working tree and one of its stages
    _project(wio)

    # When `wio trailers k3m9xq deliver architecture` prints a record, and that record
    # is the paragraph of a commit message that `wio trailers check --require` reads
    printed = wio.run(["trailers", *WORK, "architecture"])
    wio.put("msg.txt", f"feat: add x\n\n{printed.stdout}".encode())
    checked = wio.run(["trailers", "check", "--require", "msg.txt"])

    # Then both exit 0
    assert printed.exit_code == checked.exit_code == 0


@pytest.mark.channels(Channel.CLI)
def test_an_item_the_work_does_not_have_prints_no_record(wio: Wio) -> None:
    """AC-1: `--items AC-99` is refused and named."""
    # Given a Work that has no item `AC-99`
    _project(wio)

    # When `wio trailers k3m9xq deliver architecture --items AC-99` runs
    output = wio.run(["trailers", *WORK, "architecture", "--items", "AC-99"])

    # Then it exits 1, prints no record and names `AC-99`
    assert output.exit_code == 1
    assert output.stdout == ""
    assert "AC-99" in output.stderr


@pytest.mark.channels(Channel.CLI)
def test_a_stage_the_config_lacks_fails_at_commit_time(wio: Wio) -> None:
    """AC-2: `Wio-Stage: nosuch` is an error by the time of the commit."""
    # Given a commit message whose record has `Wio-Stage: nosuch`
    _project(wio)
    record = RECORD.format(work="k3m9xq", stage="nosuch")
    wio.put("msg.txt", f"feat: add x\n\n{record}\n".encode())

    # When `wio trailers check --require` reads it
    output = wio.run(["trailers", "check", "--require", "msg.txt"])

    # Then it exits 1 and names the stage
    assert output.exit_code == 1
    assert "nosuch" in output.stderr


@pytest.mark.channels(Channel.CLI)
def test_a_malformed_commit_in_a_range_fails(wio: Wio) -> None:
    """AC-2: a `Wio-Work` that is not an id fails the range, and the commit is named."""
    # Given a range in which one commit carries a `Wio-Work` value that is not a
    # valid id
    _project(wio)
    _deliver(wio, "not an id", "architecture")

    # When `wio trailers check --ref-range` reads the range
    output = wio.run(["trailers", "check", "--ref-range", "HEAD~1..HEAD"])

    # Then it exits 1 and names that commit
    head = wio.driver.git(["rev-parse", "--short", "HEAD"]).stdout.strip()
    assert output.exit_code == 1
    assert head in output.stderr


@pytest.mark.channels(Channel.CLI)
def test_a_stage_the_config_no_longer_lists_passes_a_range(wio: Wio) -> None:
    """AC-2: a well-formed record of a stage `nosuch` only warns."""
    # Given a range in which one commit has a well-formed record with `Wio-Stage:
    # nosuch`
    _project(wio)
    _deliver(wio, "k3m9xq", "nosuch")

    # When `wio trailers check --ref-range` reads the range
    output = wio.run(["trailers", "check", "--ref-range", "HEAD~1..HEAD"])

    # Then it exits 0 and warns about the stage
    assert output.exit_code == 0
    assert "warning:" in output.stderr
    assert "nosuch" in output.stderr


@pytest.mark.channels(Channel.CLI)
def test_a_redelivered_child_stays_after_the_integration_of_its_parent(
    wio: Wio,
) -> None:
    """AC-3: the two deliveries of the child are not merged across the parent."""
    # Given a range whose records are, in order, the child delivering
    # `implementation`, the parent integrating and the child delivering
    # `implementation` again
    _project(wio)
    _deliver(wio, CHILD, "implementation")
    _deliver(wio, PARENT, "integration")
    _deliver(wio, CHILD, "implementation")

    # When `wio trailers fold block` runs on the range
    output = wio.run(["trailers", "fold", "block", "HEAD~3..HEAD"])

    # Then it prints three record paragraphs in that order
    expected = [
        RECORD.format(work=CHILD, stage="implementation"),
        RECORD.format(work=PARENT, stage="integration"),
        RECORD.format(work=CHILD, stage="implementation"),
    ]
    assert output.exit_code == 0
    assert output.stdout == "\n\n".join(expected) + "\n"


@pytest.mark.channels(Channel.CLI)
def test_a_body_ends_with_the_folded_records(wio: Wio) -> None:
    """AC-3: the prose is unchanged and the records follow it."""
    # Given a body of prose and a range with a record
    _project(wio)
    _deliver(wio, "k3m9xq", "architecture")
    body = "Fix the bug.\n"

    # When `wio trailers fold body` runs on the body and the range
    output = wio.run(["trailers", "fold", "body", "HEAD~1..HEAD"], stdin=body)

    # Then it prints the prose, a blank line and the folded record
    record = RECORD.format(work="k3m9xq", stage="architecture")
    assert (output.exit_code, output.stdout) == (0, f"{body}\n{record}\n")


@pytest.mark.channels(Channel.CLI)
def test_a_gate_result_is_taken_back_by_the_check_and_the_fold(wio: Wio) -> None:
    """AC-4: the record of a gate's result passes the check and is folded."""
    # Given a human gate, a Work with an item `AC-1`, and a work commit under a pure
    # gate commit
    _project(wio)
    wio.put("note.txt", b"x\n")
    wio.commit(f"feat: add x\n\n{RECORD.format(work='k3m9xq', stage='architecture')}")
    gate = ["k3m9xq", "deliver", "architecture-review"]
    flags = ["--result", "pass", "--judge", "human", "--items", "AC-1"]
    first = wio.run(["trailers", *gate, *flags[:4]])
    wio.commit(f"chore: judge\n\n{first.stdout}", empty=True)

    # When `wio trailers k3m9xq deliver architecture-review --result pass --judge
    # human --items AC-1 --cite AC-1=pass` prints a record, that record is the
    # paragraph of a commit message that `wio trailers check --require` reads, and
    # `wio trailers fold block` runs on a range with that commit
    printed = wio.run(["trailers", *gate, *flags, "--cite", "AC-1=pass"])
    wio.put("msg.txt", f"chore: judge\n\n{printed.stdout}".encode())
    checked = wio.run(["trailers", "check", "--require", "msg.txt"])
    folded = wio.run(["trailers", "fold", "block", "HEAD~1..HEAD"])

    # Then the record holds the result, the judge and the item, the check exits 0 and
    # the fold prints a record of the gate
    lines = printed.stdout.splitlines()
    assert printed.exit_code == checked.exit_code == folded.exit_code == 0
    assert {"Wio-Result: pass", "Wio-Judge: human", "Wio-Items: AC-1"} <= set(lines)
    assert "Wio-Stage: architecture-review" in folded.stdout


@pytest.mark.channels(Channel.CLI)
def test_a_malformed_record_is_a_failed_check(wio: Wio) -> None:
    """AC-5: a `Wio-Work` that is not an id exits 1 and says so on standard error."""
    # Given a commit message with a `Wio-Work` value that is not a valid id
    _project(wio)
    record = RECORD.format(work="not an id", stage="architecture")
    wio.put("msg.txt", f"feat: add x\n\n{record}\n".encode())

    # When `wio trailers check` reads it
    output = wio.run(["trailers", "check", "msg.txt"])

    # Then it exits 1 and reports the problem on standard error
    assert output.exit_code == 1
    assert "Wio-Work" in output.stderr


@pytest.mark.channels(Channel.CLI)
@pytest.mark.parametrize(
    "call",
    [
        ["trailers", "check", "msg.txt", "--ref-range", "HEAD~1..HEAD"],
        ["trailers", "fold", "block", "nosuch..nosuch2"],
        ["trailers", "k3m9xq", "deliver"],
    ],
    ids=["path and range", "unknown revision", "no stage"],
)
def test_a_usage_error_exits_2(wio: Wio, call: list[str]) -> None:
    """AC-5: each of the three calls exits 2."""
    # Given the repository, and a message file
    _project(wio)
    wio.put("msg.txt", b"feat: add x\n")

    # When `wio trailers check msg.txt --ref-range HEAD~1..HEAD`, `wio trailers fold
    # block nosuch..nosuch2` and `wio trailers k3m9xq deliver` run
    output = wio.run(call)

    # Then each exits 2
    assert output.exit_code == 2
