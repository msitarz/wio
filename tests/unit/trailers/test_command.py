# SPDX-License-Identifier: Apache-2.0
"""Tests of the `wio trailers` command, run with fakes of its ports.

The forms run through the group, and the calls that must reach the exit code 2 or
the help run through `wio.cli.main`.

The examples use a Work `k3m9xq` with the item `AC-1` and a `deliver` that lists
`architecture` and `architecture-review`. R is the record `Wio-Work: k3m9xq`,
`Wio-Action: deliver` and `Wio-Stage: architecture`. The range `a..b` holds one
commit whose message is R, and the file `msg.txt` holds the message `feat: add x`,
which has no record.
"""

import io
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.unit.fakes import FakeStdio
from tests.unit.trailers.test_check import services
from tests.unit.trailers.test_fold import FakeHistory, _commit
from wio import cli
from wio.cli.table import Entry
from wio.trailers import TrailersCommand, describe
from wio.trailers.errors import TrailersError

if TYPE_CHECKING:
    from wio.trailers import Services

R = "Wio-Work: k3m9xq\nWio-Action: deliver\nWio-Stage: architecture"
MESSAGE = "feat: add x"


def _ports() -> Services:
    """Build the services of the command over fakes.

    Returns:
        The services, whose history holds the range `a..b` and whose file system
        holds `msg.txt`.
    """
    return services(
        history=FakeHistory((_commit(1, R),)), files={Path("msg.txt"): MESSAGE}
    )


def _form(forms: list[str], *, stdin: str = "") -> tuple[int, str, str]:
    """Run the group on the arguments after `trailers`, without the dispatch.

    Args:
        forms: The arguments after `wio trailers`.
        stdin: What standard input holds.

    Returns:
        The exit code, standard output and standard error.

    Raises:
        TrailersError: For a usage mistake, which `wio.cli` turns into exit 2.
    """
    out, err = io.StringIO(), io.StringIO()
    stdio = FakeStdio(io.StringIO(stdin), out, err)
    code = TrailersCommand(_ports()).run(Namespace(forms=forms), stdio)
    return code, out.getvalue(), err.getvalue()


def _wio(argv: list[str], *, stdin: str = "") -> tuple[int, str, str]:
    """Run `wio` with the arguments, through the real dispatch.

    Args:
        argv: The arguments after `wio`.
        stdin: What standard input holds.

    Returns:
        The exit code, standard output and standard error.
    """
    ports = _ports()
    entry = Entry("trailers", describe, lambda: TrailersCommand(ports))
    out, err = io.StringIO(), io.StringIO()
    code = cli.main(argv, FakeStdio(io.StringIO(stdin), out, err), [entry])
    return code, out.getvalue(), err.getvalue()


def test_the_write_form_prints_the_record_of_its_work() -> None:
    """AC-1: a first argument that is not a form is the Work of the write form."""
    # Given a Work `k3m9xq`
    # When `wio trailers k3m9xq deliver architecture` runs
    code, out, err = _form(["k3m9xq", "deliver", "architecture"])

    # Then it exits 0 and prints the record of `k3m9xq`
    assert (code, out, err) == (0, f"{R}\n", "")


def test_check_without_require_passes_a_message_with_no_record() -> None:
    """AC-1: the later mode of `check` needs no record."""
    # Given the message file `msg.txt`, which has no record
    # When `wio trailers check msg.txt` runs
    code, out, err = _form(["check", "msg.txt"])

    # Then it exits 0 and prints nothing
    assert (code, out, err) == (0, "", "")


@pytest.mark.parametrize("source", ["file", "standard input"])
def test_check_with_require_refuses_a_message_with_no_record(source: str) -> None:
    """AC-1: the commit-time mode of `check` needs a record."""
    # Given the message `feat: add x`, in a file and on standard input
    forms = ["check", "--require", "msg.txt" if source == "file" else "-"]

    # When `wio trailers check --require <file>` and `--require -` run
    code, out, err = _form(forms, stdin=MESSAGE)

    # Then each exits 1, prints nothing on standard output and says that no record
    # was found
    assert code == 1
    assert out == ""
    assert err == "error: 1: no record was found\n"


def test_fold_prints_the_block_and_the_body() -> None:
    """AC-1: `fold block` and `fold body` fold the records of the range."""
    # Given the range `a..b`, whose one commit has the record R, and a body
    body = "Fix it.\n"

    # When `wio trailers fold block a..b` and `fold body a..b` run
    block = _form(["fold", "block", "a..b"])
    folded = _form(["fold", "body", "a..b"], stdin=body)

    # Then each exits 0 and prints the record, the second after the body
    assert block[0] == folded[0] == 0
    assert block[1] == f"{R}\n"
    assert folded[1] == f"{body}\n{R}\n"


@pytest.mark.parametrize(
    "argv",
    [
        pytest.param(["trailers"], id="no argument"),
        pytest.param(
            ["trailers", "--items", "AC-1", "k3m9xq", "deliver", "architecture"],
            id="option before the Work",
        ),
    ],
)
def test_a_call_that_names_no_form_exits_2(argv: list[str]) -> None:
    """AC-2: no argument and an option before the first argument exit 2."""
    # Given a call that names no form
    # When it runs
    code, out, err = _wio(argv)

    # Then it exits 2, prints nothing on standard output and says what is wrong on
    # standard error
    assert code == 2
    assert out == ""
    assert "error" in err


@pytest.mark.parametrize(
    "forms",
    [["fold", "nosuch"], ["check", "--nosuch"]],
    ids=["unknown fold", "unknown option"],
)
def test_a_mistake_inside_a_form_is_a_usage_error(forms: list[str]) -> None:
    """AC-2: a form's own parse error is a `TrailersError`, which exits 2."""
    # Given a call that the chosen form does not accept
    # When the group runs it
    with pytest.raises(TrailersError):
        _form(forms)

    # Then it raises a usage error and nothing escapes as a `SystemExit`


def test_the_help_lists_the_forms() -> None:
    """AC-4: `wio trailers --help` lists the write form, `check` and `fold`."""
    # Given the command
    # When `wio trailers --help` runs
    code, out, err = _wio(["trailers", "--help"])

    # Then it exits 0 and lists the write form, `check` and `fold`
    assert (code, err) == (0, "")
    assert "<work> <action> <stage>" in out
    assert "check " in out
    assert "fold " in out


@pytest.mark.parametrize(
    "form", [["check", "-h"], ["fold", "-h"], ["fold", "block", "-h"]]
)
def test_the_help_of_a_form_is_written_and_exits_0(form: list[str]) -> None:
    """A form's `-h` prints its usage to standard output and is not an error."""
    # Given a form that is asked for its help
    # When the group runs it
    code, out, err = _form(form)

    # Then it exits 0, writes the usage of the form to standard output and nothing
    # to standard error
    assert code == 0
    assert out.startswith(f"usage: wio trailers {form[0]}")
    assert err == ""
