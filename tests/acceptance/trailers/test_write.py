# SPDX-License-Identifier: Apache-2.0
"""Scenarios of the write form of `wio trailers`, as a person or an agent sees it.

The scenarios use the project of `test_command.py`: a git repository whose config
declares the gate `architecture-review`, with `judge = "human"`, and a Work `k3m9xq`
that has an item `AC-1`. They run on the CLI channel only, because the form finds
the reviewed commit in the history of a git repository. The `review` event reaches
a sink that the CLI wires to nothing, so the events are asserted in
`tests/integration/trailers/test_write.py`.
"""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

FIXTURE = "trailers/command"
WORK = "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: architecture"
HEAD = "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: architecture-review"
GATE = f"{HEAD}\nWio-Result: pass\nWio-Judge: human"
GATE_ARGS = ["trailers", "k3m9xq", "deliver", "architecture-review"]


def _judged(wio: Wio) -> None:
    """Commit the Work, a work commit with a record and a pure gate commit on top.

    Args:
        wio: The facade.
    """
    wio.fixture(FIXTURE)
    wio.commit("feat: add the Work")
    wio.put("note.txt", b"x\n")
    wio.commit(f"feat: add x\n\n{WORK}")
    wio.commit(f"chore: judge\n\n{GATE}", empty=True)


@pytest.mark.channels(Channel.CLI)
def test_a_human_gate_takes_both_judges_and_no_reviewed_commit_is_refused(
    wio: Wio,
) -> None:
    """AC-1: an agent and then a human record a human gate; no reviewed commit fails."""
    # Given a human gate with a work commit under a pure gate commit
    _judged(wio)

    # When `wio trailers k3m9xq deliver architecture-review --result pass` runs, then
    # the same with `--judge human`
    agent = wio.run([*GATE_ARGS, "--result", "pass"])
    human = wio.run([*GATE_ARGS, "--result", "pass", "--judge", "human"])

    # Then each exits 0, the first prints the record with `Wio-Judge: agent` and the
    # second with `Wio-Judge: human`
    assert (agent.exit_code, agent.stdout) == (
        0,
        f"{HEAD}\nWio-Result: pass\nWio-Judge: agent\n",
    )
    assert (human.exit_code, human.stdout) == (0, f"{GATE}\n")


@pytest.mark.channels(Channel.CLI)
def test_a_history_with_no_reviewed_commit_is_refused(wio: Wio) -> None:
    """AC-1: every commit is a pure gate commit, so there is nothing reviewed."""
    # Given a repository whose only commit is a pure gate commit of the gate
    wio.fixture(FIXTURE)
    wio.commit(f"chore: judge\n\n{GATE}")

    # When `wio trailers k3m9xq deliver architecture-review --result pass --judge
    # human` runs
    output = wio.run([*GATE_ARGS, "--result", "pass", "--judge", "human"])

    # Then it exits 1, prints no record and names the missing reviewed commit
    assert output.exit_code == 1
    assert output.stdout == ""
    assert "no reviewed commit" in output.stderr


@pytest.mark.channels(Channel.CLI)
def test_a_result_outside_the_vocabulary_prints_no_record(wio: Wio) -> None:
    """AC-2: `--result maybe` is refused."""
    # Given the repository with a gate commit, and a config whose results are
    # `pass`, `fail` and `unknown`
    _judged(wio)

    # When `wio trailers k3m9xq deliver architecture-review --result maybe` runs
    output = wio.run([*GATE_ARGS, "--result", "maybe"])

    # Then it exits 1, prints no record and names the result
    assert output.exit_code == 1
    assert output.stdout == ""
    assert "maybe" in output.stderr


@pytest.mark.channels(Channel.CLI)
def test_a_gate_result_prints_the_items_it_cited(wio: Wio) -> None:
    """AC-3: the record holds the result, the judge and the items."""
    # Given a human gate with a work commit under a pure gate commit, and a Work with
    # an item `AC-1`
    _judged(wio)

    # When `wio trailers k3m9xq deliver architecture-review --result pass --judge
    # human --items AC-1 --cite AC-1=pass` runs
    output = wio.run(
        [*GATE_ARGS, "--result", "pass", "--judge", "human"]
        + ["--items", "AC-1", "--cite", "AC-1=pass"]
    )

    # Then it exits 0 and prints the record with `Wio-Result: pass`, `Wio-Judge:
    # human` and `Wio-Items: AC-1`
    lines = output.stdout.splitlines()
    assert output.exit_code == 0
    assert {"Wio-Result: pass", "Wio-Judge: human", "Wio-Items: AC-1"} <= set(lines)
