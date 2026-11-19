# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio trailers`, the command that runs its three forms.

The scenarios use a git repository whose config declares the gate
`architecture-review`, with `judge = "human"`, and a Work `k3m9xq` that has an item
`AC-1` and a `deliver` that lists `architecture` and `architecture-review`. They run
on the CLI channel only, because the in-process channel has no git repository.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox

FIXTURE = "trailers/command"
R = "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: architecture"
GATE = (
    "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: architecture-review\n"
    "Wio-Result: pass\nWio-Judge: human"
)
MESSAGE = "feat: add x\n"


def _project(wio: Wio, *, record: str | None = R) -> None:
    """Start from the project, committed, and commit one more with a record.

    Args:
        wio: The facade.
        record: The record that `HEAD` carries, or `None` for a message without
            one.
    """
    wio.fixture(FIXTURE)
    wio.commit("feat: add the Work")
    wio.put("note.txt", b"x\n")
    body = "feat: add x" if record is None else f"feat: add x\n\n{record}"
    wio.commit(body)


@pytest.mark.channels(Channel.CLI)
def test_the_arguments_select_the_form(wio: Wio) -> None:
    """AC-1: the write form, `check` and `fold` run from the first argument."""
    # Given the repository, a commit message file with the subject `feat: add x` and
    # no record, and a pull request body. Standard input holds the message for the
    # fourth run and the body for the sixth
    _project(wio)
    wio.put("msg.txt", MESSAGE.encode())
    body = "Fix the bug.\n"

    # When `wio trailers k3m9xq deliver architecture`, `wio trailers check <file>`,
    # `wio trailers check --require <file>`, `wio trailers check --require -` with
    # the message on standard input, `wio trailers fold block HEAD~1..HEAD` and
    # `wio trailers fold body HEAD~1..HEAD` run
    written = wio.run(["trailers", "k3m9xq", "deliver", "architecture"])
    later = wio.run(["trailers", "check", "msg.txt"])
    required = wio.run(["trailers", "check", "--require", "msg.txt"])
    piped = wio.run(["trailers", "check", "--require", "-"], stdin=MESSAGE)
    block = wio.run(["trailers", "fold", "block", "HEAD~1..HEAD"])
    folded = wio.run(["trailers", "fold", "body", "HEAD~1..HEAD"], stdin=body)

    # Then the first, the fifth and the sixth exit 0 and print the record of
    # `k3m9xq`, the folded record of `HEAD` and the body with that record at its end
    # in turn, the second exits 0 because a message without a record passes, and the
    # third and the fourth exit 1 because it has none
    assert (written.exit_code, written.stdout) == (0, f"{R}\n")
    assert (block.exit_code, block.stdout) == (0, f"{R}\n")
    assert (folded.exit_code, folded.stdout) == (0, f"{body}\n{R}\n")
    assert (later.exit_code, later.stdout) == (0, "")
    assert (required.exit_code, required.stdout) == (1, "")
    assert (piped.exit_code, piped.stdout) == (1, "")


@pytest.mark.channels(Channel.CLI)
@pytest.mark.parametrize(
    "call",
    [
        ["trailers"],
        ["trailers", "fold", "nosuch"],
        ["trailers", "check", "--nosuch"],
        ["trailers", "--items", "AC-1", "k3m9xq", "deliver", "architecture"],
    ],
    ids=["no argument", "unknown fold", "unknown option", "option before the Work"],
)
def test_a_usage_mistake_exits_2(wio: Wio, call: list[str]) -> None:
    """AC-2: each call that no form accepts exits 2 and says what is wrong."""
    # Given the repository
    _project(wio)

    # When `wio trailers`, `wio trailers fold nosuch`, `wio trailers check
    # --nosuch` and the call that starts with the option `--items AC-1`, before
    # `k3m9xq deliver architecture`, run
    output = wio.run(call)

    # Then each exits 2, prints nothing on standard output and says on standard
    # error what is wrong
    assert output.exit_code == 2
    assert output.stdout == ""
    assert "error" in output.stderr


@pytest.mark.channels(Channel.CLI)
def test_a_record_round_trips_through_the_real_adapters(wio: Wio) -> None:
    """AC-3: the printed record is checked and folded from a real commit."""
    # Given the repository, and no injected adapter
    wio.fixture(FIXTURE)
    wio.commit("feat: add the Work")

    # When `wio trailers k3m9xq deliver architecture` prints a record, a commit
    # carries it in its message, and `wio trailers check --ref-range HEAD~1..HEAD`
    # and `wio trailers fold block HEAD~1..HEAD` run
    printed = wio.run(["trailers", "k3m9xq", "deliver", "architecture"])
    wio.put("note.txt", b"x\n")
    wio.commit(f"feat: add x\n\n{printed.stdout}")
    checked = wio.run(["trailers", "check", "--ref-range", "HEAD~1..HEAD"])
    folded = wio.run(["trailers", "fold", "block", "HEAD~1..HEAD"])

    # Then each exits 0 and the fold prints that record
    assert printed.exit_code == checked.exit_code == folded.exit_code == 0
    assert folded.stdout == printed.stdout


@pytest.mark.channels(Channel.CLI)
def test_a_gate_result_with_logging_off_leaves_the_wio_home_empty(
    wio: Wio, sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Append-event AC-3 keeps the command result when logging is off.

    Args:
        wio: Runs the real trailers command.
        sandbox: Supplies an isolated Wio home.
        monkeypatch: Sets the opt-out in the command environment.
    """
    # Given the repository, with a work commit under a pure gate commit of
    # `architecture-review`, an empty Wio home and logging switched off.
    _project(wio)
    wio.commit(f"chore: judge\n\n{GATE}", empty=True)
    home = Path(sandbox.env["WIO_HOME"])
    monkeypatch.setitem(sandbox.env, "WIO_LOG", "off")

    # When `wio trailers k3m9xq deliver architecture-review --result pass --judge
    # human` runs
    output = wio.run(
        ["trailers", "k3m9xq", "deliver", "architecture-review"]
        + ["--result", "pass", "--judge", "human"]
    )

    # Then it prints the record, exits 0 and leaves the Wio home empty
    assert (output.exit_code, output.stdout, output.stderr) == (0, f"{GATE}\n", "")
    assert not home.exists()


@pytest.mark.channels(Channel.CLI)
def test_a_cited_rule_code_is_refused_by_the_null_rules_port(wio: Wio) -> None:
    """AC-3: `docs.DOC001` is not selected by any stage, so it is refused."""
    # Given the repository, with no injected adapter
    _project(wio)
    wio.commit(f"chore: judge\n\n{GATE}", empty=True)

    # When `wio trailers k3m9xq deliver architecture-review --result pass --judge
    # human --cite docs.DOC001=fail` runs
    output = wio.run(
        ["trailers", "k3m9xq", "deliver", "architecture-review"]
        + ["--result", "pass", "--judge", "human", "--cite", "docs.DOC001=fail"]
    )

    # Then it exits 1, prints an `error:` line that names `docs.DOC001` on standard
    # error and prints nothing on standard output
    assert output.exit_code == 1
    assert output.stdout == ""
    assert "error: docs.DOC001:" in output.stderr


@pytest.mark.channels(Channel.CLI)
def test_the_help_lists_the_forms(wio: Wio) -> None:
    """AC-4: `wio trailers --help` lists the write form, `check` and `fold`."""
    # Given the repository
    _project(wio)

    # When `wio trailers --help` runs
    output = wio.run(["trailers", "--help"])

    # Then it exits 0 and lists the write form, `check` and `fold`
    assert output.exit_code == 0
    assert "<work> <action> <stage>" in output.stdout
    assert "check " in output.stdout
    assert "fold " in output.stdout
