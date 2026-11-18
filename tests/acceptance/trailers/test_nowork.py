# SPDX-License-Identifier: Apache-2.0
"""Scenarios of the `none` form of `wio trailers`, the record of a commit with no Work.

The scenarios use the project of `test_command.py`: a git repository whose config
declares the action `deliver` and the stage `architecture`, and a Work `k3m9xq`.
They run on the CLI channel only, because the command finds the repository with git.
"""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

FIXTURE = "trailers/command"
STUB = pytest.mark.skip(reason="architecture stub: the form is declared in nowork.pyi")


def _project(wio: Wio) -> None:
    """Start from the project, committed.

    Args:
        wio: The facade.
    """
    wio.fixture(FIXTURE)
    wio.commit("feat: add the Work")


@STUB
@pytest.mark.channels(Channel.CLI)
def test_a_record_for_no_work_is_printed_and_accepted_by_the_check(wio: Wio) -> None:
    """AC-1: the printed record is the paragraph that `check --require` accepts."""
    # Given the repository
    _project(wio)

    # When `wio trailers none` runs, and its output is the paragraph of a commit
    # message that `wio trailers check --require` reads
    printed = wio.run(["trailers", "none"])
    wio.put("msg.txt", f"chore: tidy\n\n{printed.stdout}".encode())
    checked = wio.run(["trailers", "check", "--require", "msg.txt"])

    # Then the first prints exactly `Wio-Work: none` and a newline and exits 0, and
    # the second exits 0
    assert (printed.exit_code, printed.stdout) == (0, "Wio-Work: none\n")
    assert checked.exit_code == 0


@STUB
@pytest.mark.channels(Channel.CLI)
@pytest.mark.parametrize(
    "call",
    [
        ["trailers", "none", "deliver", "architecture"],
        ["trailers", "none", "--items", "AC-1"],
        ["trailers", "none", "--result", "pass"],
    ],
    ids=["action and stage", "items", "result"],
)
def test_a_none_with_anything_more_is_refused(wio: Wio, call: list[str]) -> None:
    """AC-2: an action, a stage or an option after `none` exits 2."""
    # Given the repository
    _project(wio)

    # When `wio trailers none deliver architecture`, `wio trailers none --items AC-1`
    # and `wio trailers none --result pass` run
    output = wio.run(call)

    # Then each exits 2, prints nothing on standard output and says on standard
    # error what is wrong
    assert output.exit_code == 2
    assert output.stdout == ""
    assert "error" in output.stderr


@STUB
@pytest.mark.channels(Channel.CLI)
@pytest.mark.parametrize(
    "call",
    [
        ["trailers", "k3m9xq,a7b2c4", "deliver", "architecture"],
        ["trailers", "none,k3m9xq", "deliver", "architecture"],
    ],
    ids=["two Works", "none and a Work"],
)
def test_a_list_of_works_is_refused(wio: Wio, call: list[str]) -> None:
    """AC-3: a comma list exits 2 and asks for one Work."""
    # Given the repository and a Work `k3m9xq`
    _project(wio)

    # When `wio trailers k3m9xq,a7b2c4 deliver architecture` and `wio trailers
    # none,k3m9xq deliver architecture` run
    output = wio.run(call)

    # Then each exits 2, prints nothing on standard output and says on standard
    # error that a list of Works is not written and asks for one Work
    assert output.exit_code == 2
    assert output.stdout == ""
    assert "list of Works" in output.stderr
    assert "name one Work" in output.stderr


@STUB
@pytest.mark.channels(Channel.CLI)
def test_a_config_that_cannot_be_read_exits_2(wio: Wio) -> None:
    """AC-4: `none` is wired like the other forms, so a bad config stops it."""
    # Given a repository whose config is not valid TOML
    _project(wio)
    wio.put(".agents/wio/config.toml", b"this is [not toml\n")

    # When `wio trailers none` runs
    output = wio.run(["trailers", "none"])

    # Then the command exits 2 and prints nothing on standard output
    assert output.exit_code == 2
    assert output.stdout == ""
